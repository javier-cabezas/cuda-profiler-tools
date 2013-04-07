# Author: Javier Cabezas <javier.cabezas@bsc.es>
#
# Copyright (c) 2013 Barcelona Supercomputing Center
#                    IMPACT Research Group
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import copy

from cudaprof.common import Counter, Metric, Option
from cudaprof.libs import C, CUDA, CUPTI

CUDA_FAKE_CONTEXT = None

GPUS = 0

MAX_STRING_LEN = 1024

PROFILER_OPTIONS = {
    'gpustarttimestamp'     : Option('gpustarttimestamp',
                                     'Time stamp when a kernel or memory transfer starts.'),
    'gpuendtimestamp'       : Option('gpuendtimestamp',
                                     'Time stamp when a kernel or memory transfer completes.'),
    'timestamp'             : Option('timestamp',
                                     'Time stamp when a kernel or memory transfer starts. The values are single precision floating point value in microseconds. Use of the gpustarttimestamp is recommended as this provides a more accurate time stamp.'),
    'gridsize'              : Option('gridsize',
                                     'Number of blocks in a grid along the X and Y dimensions for a kernel launch.'),
    'gridsize3d'            : Option('gridsize3d',
                                     'Number of blocks in a grid along the X, Y and Z dimensions for a kernel launch.'),
    'threadblocksize'       : Option('threadblocksize',
                                     'Number of threads in a block along the X, Y and Z dimensions for a kernel launch.'),
    'dynsmemperblock'       : Option('dynsmemperblock',
                                     'Size of dynamically allocated shared memory per block in bytes for a kernel launch.'),
    'stasmemperblock'       : Option('stasmemperblock',
                                     'Size of statically allocated shared memory per block in bytes for a kernel launch.'),
    'regperthread'          : Option('regperthread',
                                     'Number of registers used per thread for a kernel launch.'),
    'memtransferdir'        : Option('memtransferdir',
                                     'Memory transfer direction, a direction value of 0 is used for host to device memory copies and a value of 1 is used for device to host memory copies.'),
    'memtransfersize'       : Option('memtransfersize',
                                     'Memory transfer size in bytes. This option shows the amount of memory transferred between source (host/device) to destination (host/device).'),
    'memtransferhostmemtype': Option('memtransferhostmemtype',
                                     'Host memory type (pageable or page-locked). This option implies whether during a memory transfer, the host memory type is pageable or page-locked.'),
    'streamid'              : Option('streamid',
                                     'Stream Id for a kernel launch or a memory transfer.'),
    'cacheconfigrequested'  : Option('cacheconfigrequested',
                                     'Requested cache configuration option for a kernel launch:\n'+
                                     '  - 0 CU_FUNC_CACHE_PREFER_NONE - no preference for shared memory or L1 (default)\n'+
                                     '  - 1 CU_FUNC_CACHE_PREFER_SHARED - prefer larger shared memory and smaller L1 cache\n'+
                                     '  - 2 CU_FUNC_CACHE_PREFER_L1 - prefer larger L1 cache and smaller shared memory\n'+
                                     '  - 3 CU_FUNC_CACHE_PREFER_EQUAL - prefer equal sized L1 cache and shared memory'),
    'cacheconfigexecuted'   : Option('cacheconfigexecuted',
                                     'Cache configuration which was used for the kernel launch. The values are same as those listed under cacheconfigrequested.'),
    'countermodeaggregate'  : Option('countermodeaggregate',
                                     'If this option is selected then aggregate counter values will be output. For a SM counter the counter value is the sum of the counter values from all SMs. For l1*, tex*, sm_cta_launched, uncached_global_load_transaction and global_store_transaction counters the counter value is collected for 1 SM from each GPC and it is extrapolated for all SMs. This option is supported only for CUDA devices with compute capability 2.0 or higher.'),
    'conckerneltrace'       : Option('conckerneltrace',
                                     'This option should be used to get gpu start and end timestamp values in case of concurrent kernels. Without this option execution of concurrent kernels is serialized and the timestamps are not correct. Only CUDA devices with compute capability 2.0 or higher support execution of multiple kernels concurrently. When this option is enabled additional code is inserted for each kernel and this will result in some additional execution overhead. This option cannot be used along with profiler counters. In case some counter is given in the configuration file along with "conckerneltrace" then a warning is printed in the profiler output file and the counter will not be enabled.'),
    'enableonstart'         : Option('enableonstart',
                                             'Use enableonstart 1 option to enable or enableonstart 0 to disable profiling from the start of application execution. If this option is not used then by default profiling is enabled from the start. To limit profiling to a region of your application, CUDA provides functions to start and stop profile data collection. cudaProfilerStart() is used to start profiling and cudaProfilerStop() is used to stop profiling (using the CUDA driver API, you get the same functionality with cuProfilerStart() and cuProfilerStop()). When using the start and stop functions, you also need to instruct the profiling tool to disable profiling at the start of the application. For command line profiler you do this by adding enableonstart 0 in the profiler configuration file.',
                                             1)
}

def init():
    global CUDA_FAKE_CONTEXT
    global GPUS

    # Initialize libs.CUDA
    CUDA.cuInit(0)

    # Get number of GPUs in the system
    GPUS = C.c_int(0)
    CUDA.cuDeviceGetCount(C.byref(GPUS))

    # Iterate for each GPU
    p = C.create_string_buffer(256)
    for gpu in range(GPUS.value):
        CUDA.cuDeviceGetName(p, 256, gpu)
        major = C.c_int(0)
        minor = C.c_int(0)
        CUDA.cuDeviceComputeCapability(C.byref(major), C.byref(minor), gpu)


    # Create a libs.CUDA context needed for event profiling
    CUDA_FAKE_CONTEXT = C.c_void_p(0)
    CUDA.cuCtxCreate_v2(C.byref(CUDA_FAKE_CONTEXT), 0, 0)

def is_valid_output_pattern(pattern):
    return pattern.count('%d') == 1

def get_options():
    return copy.deepcopy(list(PROFILER_OPTIONS.values()))


def get_counters(by_domain):
    counters = {}

    # Get number of event domains
    ndomains = C.c_uint32()
    CUPTI.cuptiDeviceGetNumEventDomains(0, C.byref(ndomains))

    # Enumerate event domains
    domains = (CUPTI.domain_t * ndomains.value)()
    nbytes = C.c_size_t(ndomains.value * C.sizeof(CUPTI.domain_t))
    CUPTI.cuptiDeviceEnumEventDomains(0,
                                      C.byref(nbytes),
                                      C.cast(domains, C.POINTER(CUPTI.domain_t)))

    # Iterate for each event domain
    p = C.create_string_buffer(MAX_STRING_LEN)
    for domain in domains:
        # Get event domain name
        nbytes = C.c_size_t(MAX_STRING_LEN)
        CUPTI.cuptiDeviceGetEventDomainAttribute(0,
                                                 domain,
                                                 CUPTI.domain_attr.NAME,
                                                 C.byref(nbytes),
                                                 p)
        domain_name = p.value

        # Get event domain profiled instances
        nbytes = C.c_size_t(C.sizeof(C.c_uint32))
        value = C.c_uint32()
        CUPTI.cuptiDeviceGetEventDomainAttribute(0,
                                                 domain,
                                                 CUPTI.domain_attr.INSTANCE_COUNT,
                                                 C.byref(nbytes),
                                                 C.byref(value))
        domain_instances_profiled = value.value

        # Get event domain total instances
        nbytes = C.c_size_t(C.sizeof(C.c_uint32))
        value = C.c_uint32()
        CUPTI.cuptiDeviceGetEventDomainAttribute(0,
                                                 domain,
                                                 CUPTI.domain_attr.TOTAL_INSTANCE_COUNT,
                                                 C.byref(nbytes),
                                                 C.byref(value))
        domain_instances_total = value.value

        print domain_name, domain_instances_profiled, domain_instances_total

        # If group per event domain
        if by_domain:
            counters[domain_name] = list()

        # Get number of events in the domain
        nevents = C.c_uint32()
        CUPTI.cuptiEventDomainGetNumEvents(domain, C.byref(nevents))

        # Enumerate events in the domain
        events = (CUPTI.event_t * nevents.value)()
        nbytes = C.c_size_t(nevents.value * C.sizeof(CUPTI.event_t))
        CUPTI.cuptiEventDomainEnumEvents(domain,
                                         C.byref(nbytes),
                                         C.cast(events, C.POINTER(CUPTI.event_t)))

        # Iterate for each event domain
        p = C.create_string_buffer(MAX_STRING_LEN)
        for event in events:
            nbytes = C.c_size_t(MAX_STRING_LEN)
            CUPTI.cuptiEventGetAttribute(event,
                                         CUPTI.event_attr.NAME,
                                         C.byref(nbytes),
                                         p)
            name = p.value

            nbytes = C.c_size_t(MAX_STRING_LEN)
            CUPTI.cuptiEventGetAttribute(event,
                                         CUPTI.event_attr.LONG_DESCRIPTION,
                                         C.byref(nbytes),
                                         p)
            description = p.value

            cat = C.c_int()
            nbytes = C.c_size_t(C.sizeof(C.c_int))
            CUPTI.cuptiEventGetAttribute(event,
                                         CUPTI.event_attr.CATEGORY,
                                         C.byref(nbytes),
                                         C.byref(cat))
            category = cat.value

            # Create a new Counter
            c = Counter(name, description, category, event)

            if by_domain:
                # If group per event domain
                counters[domain_name].append(c)
            else:
                # If group per event category
                category = Counter.CATEGORIES[c.category]
                if not counters.has_key(category):
                    counters[category] = list()
                else:
                    counters[category].append(c)

    return counters


def get_event_groups(counters):
    if len(counters) == 0:
        return [[]]

    counter_groups = []
    # Collect event id's
    event_ids = [ event.id for event in counters ]

    # Create group sets for the events
    groups_ptr = C.POINTER(CUPTI.group_sets)()
    events = (CUPTI.event_t * len(counters))(*event_ids)
    nbytes = C.c_size_t(C.sizeof(CUPTI.event_t) * len(counters))

    CUPTI.cuptiEventGroupSetsCreate(CUDA_FAKE_CONTEXT,
                                    nbytes,
                                    events,
                                    C.byref(groups_ptr))

    # Iterate for each group set
    groupsets_desc = groups_ptr[0]
    for groupset in range(groupsets_desc.numSets):
        groupset_desc = groupsets_desc.sets[groupset]

        # Iterate for each group within the group set
        for group in range(groupset_desc.numEventGroups):
            group_desc = groupset_desc.eventGroups[group]

            # Get number of events in the group
            nevents = C.c_uint32()
            nbytes = C.c_size_t(C.sizeof(C.c_uint32))
            CUPTI.cuptiEventGroupGetAttribute(group_desc,
                                              CUPTI.event_group_attr.NUM_EVENTS,
                                              C.byref(nbytes),
                                              C.byref(nevents))

            # Enumerate events in the group
            events = (CUPTI.event_t * nevents.value)()
            nbytes = C.c_size_t(nevents.value * C.sizeof(CUPTI.event_t))
            CUPTI.cuptiEventGroupGetAttribute(group_desc,
                                              CUPTI.event_group_attr.EVENTS,
                                              C.byref(nbytes),
                                              C.cast(events, C.POINTER(CUPTI.event_t)))

            # Collect the Counters for the events in the group
            counter_group = [ counter for counter in counters if counter.id in events ]
            counter_groups.append(counter_group)

    # Free used resources
    CUPTI.cuptiEventGroupSetsDestroy(groups_ptr)

    return counter_groups


def get_metrics():
    metrics_ret = {}

    # Get number of metrics
    nmetrics = C.c_uint32()
    CUPTI.cuptiDeviceGetNumMetrics(0, C.byref(nmetrics))

    # Enumerate metrics
    metrics = (CUPTI.metric_t * nmetrics.value)()
    nbytes = C.c_size_t(nmetrics.value * C.sizeof(CUPTI.metric_t))
    CUPTI.cuptiDeviceEnumMetrics(0,
                                 C.byref(nbytes),
                                 C.cast(metrics, C.POINTER(CUPTI.metric_t)))

    # Iterate for each metric
    p = C.create_string_buffer(MAX_STRING_LEN)
    for metric in metrics:
        nbytes = C.c_size_t(MAX_STRING_LEN)
        CUPTI.cuptiMetricGetAttribute(metric,
                                      CUPTI.metric_attr.NAME,
                                      C.byref(nbytes),
                                      p)
        name = p.value

        nbytes = C.c_size_t(MAX_STRING_LEN)
        CUPTI.cuptiMetricGetAttribute(metric,
                                      CUPTI.metric_attr.LONG_DESCRIPTION,
                                      C.byref(nbytes),
                                      p)
        description = p.value

        cat = C.c_int()
        nbytes = C.c_size_t(C.sizeof(C.c_int))
        CUPTI.cuptiMetricGetAttribute(metric,
                                      CUPTI.metric_attr.CATEGORY,
                                      C.byref(nbytes),
                                      C.byref(cat))
        category = cat.value

        # Get number of events for the metric
        nevents = C.c_uint32()
        CUPTI.cuptiMetricGetNumEvents(metric, C.byref(nevents))

        # Enumerate events
        events = (CUPTI.event_t * nevents.value)()
        nbytes = C.c_size_t(nevents.value * C.sizeof(CUPTI.event_t))
        CUPTI.cuptiMetricEnumEvents(metric,
                                    C.byref(nbytes),
                                    C.cast(events, C.POINTER(CUPTI.event_t)))

        event_names = []

        for event in events:
            nbytes = C.c_size_t(MAX_STRING_LEN)
            CUPTI.cuptiEventGetAttribute(event,
                                         CUPTI.event_attr.NAME,
                                         C.byref(nbytes),
                                         p)
            event_names.append(p.value)

        # Create a new Metric
        m = Metric(name, description, category, metric, event_names)

        # Group per metric category
        category = Metric.CATEGORIES[m.category]
        if not metrics_ret.has_key(category):
            metrics_ret[category] = list()
        else:
            metrics_ret[category].append(m)

    return metrics_ret


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
