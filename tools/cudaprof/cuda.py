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

import common
import libs

C = libs.C

CUDA_FAKE_CONTEXT = None

GPUS = 0

MAX_STRING_LEN = 1024

PROFILER_OPTIONS = {
    'gpustarttimestamp'     : common.Option('gpustarttimestamp'     ),
    'gpuendtimestamp'       : common.Option('gpuendtimestamp'       ),
    'timestamp'             : common.Option('timestamp'             ),
    'gridsize'              : common.Option('gridsize'              ),
    'gridsize3d'            : common.Option('gridsize3d'            ),
    'threadblocksize'       : common.Option('threadblocksize'       ),
    'dynsmemperblock'       : common.Option('dynsmemperblock'       ),
    'stasmemperblock'       : common.Option('stasmemperblock'       ),
    'regperthread'          : common.Option('regperthread'          ),
    'memtransferdir'        : common.Option('memtransferdir'        ),
    'memtransfersize'       : common.Option('memtransfersize'       ),
    'memtransferhostmemtype': common.Option('memtransferhostmemtype'),
    'streamid'              : common.Option('streamid'              ),
    'cacheconfigrequested'  : common.Option('cacheconfigrequested'  ),
    'cacheconfigexecuted'   : common.Option('cacheconfigexecuted'   ),
    'countermodeaggregate'  : common.Option('countermodeaggregate'  ),
    'conckerneltrace'       : common.Option('conckerneltrace'       ),
    'enableonstart'         : common.Option('enableonstart'         , 1)
}

def init():
    global CUDA_FAKE_CONTEXT
    global GPUS

    # Load libraries into memory
    libs.load_libraries()

    # Initialize libs.CUDA
    libs.CUDA.cuInit(0)

    # Get number of GPUs in the system
    GPUS = C.c_int(0)
    libs.CUDA.cuDeviceGetCount(C.byref(GPUS))

    # Iterate for each GPU
    p = C.create_string_buffer(256)
    for gpu in range(GPUS.value):
        libs.CUDA.cuDeviceGetName(p, 256, gpu)
        major = C.c_int(0)
        minor = C.c_int(0)
        libs.CUDA.cuDeviceComputeCapability(C.byref(major), C.byref(minor), gpu)


    # Create a libs.CUDA context needed for event profiling
    CUDA_FAKE_CONTEXT = C.c_void_p(0)
    libs.CUDA.cuCtxCreate_v2(C.byref(CUDA_FAKE_CONTEXT), 0, 0)

def is_valid_output_pattern(pattern):
    return pattern.count('%d') == 1

def get_options():
    return copy.deepcopy(list(PROFILER_OPTIONS.values()))


def get_counters(by_domain):
    counters = {}

    # Get number of event domains
    ndomains = C.c_uint32()
    libs.CUPTI.cuptiDeviceGetNumEventDomains(0, C.byref(ndomains))

    # Enumerate event domains
    domains = (libs.CUPTI.domain_t * ndomains.value)()
    nbytes = C.c_size_t(ndomains.value * C.sizeof(libs.CUPTI.domain_t))
    libs.CUPTI.cuptiDeviceEnumEventDomains(0, C.byref(nbytes),
                                              C.cast(domains, C.POINTER(libs.CUPTI.domain_t)))

    # Iterate for each event domain
    p = C.create_string_buffer(MAX_STRING_LEN)
    for domain in domains:
        # Get event domain name
        nbytes = C.c_size_t(MAX_STRING_LEN)
        libs.CUPTI.cuptiEventDomainGetAttribute(domain,
                                                libs.CUPTI.domain_attr.NAME,
                                                C.byref(nbytes),
                                                p)
        domain_name = p.value

        # If group per event domain
        if by_domain:
            counters[domain_name] = list()

        # Get number of events in the domain
        nevents = C.c_uint32()
        libs.CUPTI.cuptiEventDomainGetNumEvents(domain, C.byref(nevents))

        # Enumerate events in the domain
        events = (libs.CUPTI.event_t * nevents.value)()
        nbytes = C.c_size_t(nevents.value * C.sizeof(libs.CUPTI.event_t))
        libs.CUPTI.cuptiEventDomainEnumEvents(domain,
                                              C.byref(nbytes),
                                              C.cast(events, C.POINTER(libs.CUPTI.event_t)))

        # Iterate for each event domain
        p = C.create_string_buffer(MAX_STRING_LEN)
        for event in events:
            nbytes = C.c_size_t(MAX_STRING_LEN)
            libs.CUPTI.cuptiEventGetAttribute(event, libs.CUPTI.event_attr.NAME, C.byref(nbytes), p)
            name = p.value

            nbytes = C.c_size_t(MAX_STRING_LEN)
            libs.CUPTI.cuptiEventGetAttribute(event, libs.CUPTI.event_attr.LONG_DESCRIPTION, C.byref(nbytes), p)
            description = p.value

            cat = C.c_int()
            nbytes = C.c_size_t(C.sizeof(C.c_int))
            libs.CUPTI.cuptiEventGetAttribute(event, libs.CUPTI.event_attr.CATEGORY, C.byref(nbytes), C.byref(cat))
            category = cat.value

            # Create a new Counter
            c = common.Counter(name, description, category, event)

            if by_domain:
                # If group per event domain
                counters[domain_name].append(c)
            else:
                # If group per event category
                category = common.COUNTER_CATEGORIES[c.category]
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
    groups_ptr = C.POINTER(libs.cupti_group_sets)()
    events = (libs.CUPTI.event_t * len(counters))(*event_ids)
    nbytes = C.c_size_t(C.sizeof(libs.CUPTI.event_t) * len(counters))

    libs.CUPTI.cuptiEventGroupSetsCreate(CUDA_FAKE_CONTEXT,
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
            libs.CUPTI.cuptiEventGroupGetAttribute(group_desc,
                                                   libs.CUPTI.event_group_attr.NUM_EVENTS,
                                                   C.byref(nbytes),
                                                   C.byref(nevents))

            # Enumerate events in the group
            events = (libs.CUPTI.event_t * nevents.value)()
            nbytes = C.c_size_t(nevents.value * C.sizeof(libs.CUPTI.event_t))
            libs.CUPTI.cuptiEventGroupGetAttribute(group_desc,
                                                   libs.CUPTI.event_group_attr.EVENTS,
                                                   C.byref(nbytes),
                                                   C.cast(events, C.POINTER(libs.CUPTI.event_t)))

            # Collect the Counters for the events in the group
            counter_group = [ counter for counter in counters if counter.id in events ]
            counter_groups.append(counter_group)

    # Free used resources
    libs.CUPTI.cuptiEventGroupSetsDestroy(groups_ptr)

    return counter_groups





# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
