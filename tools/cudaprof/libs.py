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

import ctypes as C
import sys

from cudaprof.common import enum

CUDA = None
CUPTI = None

def register_cuda(f, args):
    global CUDA

    f.argtypes = args
    f.restype  = CUDA.result_t

    f_orig = f
    def wrapper(*my_args):
        res = f_orig(*my_args)

        if res != 0:
            print 'CUDA: Error "%d" calling %s' % (res, f)

    f = wrapper


def register_cupti(f, args):
    global CUPTI

    f.argtypes = args
    f.restype  = CUPTI.result_t

    f_orig = f
    def wrapper(*my_args):
        res = f_orig(*my_args)

        if res != 0:
            print 'CUPTI: Error "%d" calling %s' % (res, f)

    f = wrapper


class cupti_group_set(C.Structure):
    _fields_ = [("numEventGroups", C.c_uint32),
                ("eventGroups", C.POINTER(C.c_void_p))]


class cupti_group_sets(C.Structure):
    _fields_ = [("numSets", C.c_uint32),
                ("sets", C.POINTER(cupti_group_set))]


class cupti_metric_value(C.Union):
    _fields_ = [("metricValueDouble", C.c_double),
                ("metricValueUint64", C.c_uint64),
                ("metricValuePercent", C.c_double),
                ("metricValueThroughput", C.c_uint64)]

    def get_value(self, kind):
        if kind == CUPTI.metric_value_kind.DOUBLE:
            return self.metricValueDouble
        elif kind == CUPTI.metric_value_kind.UINT64:
            return self.metricValueUint64
        elif kind == CUPTI.metric_value_kind.PERCENT:
            return self.metricValuePercent
        elif kind == CUPTI.metric_value_kind.THROUGHPUT:
            return self.metricValueThroughput
        else:
            assert False, 'Wrong metric value kind'


def init_libcuda():
    # Interpose all needed CUDA functions
    register_cuda(CUDA.cuInit,
                  [ C.c_uint ])

    register_cuda(CUDA.cuDeviceGetCount,
                  [ C.POINTER(C.c_int) ])

    register_cuda(CUDA.cuDeviceGetName,
                  [ C.POINTER(C.c_char), C.c_int, CUDA.device_t ])

    register_cuda(CUDA.cuDeviceComputeCapability,
                  [ C.POINTER(C.c_int), C.POINTER(C.c_int), CUDA.device_t ])

    register_cuda(CUDA.cuCtxCreate_v2,
                  [ C.c_void_p, C.c_uint, CUDA.device_t ])

    register_cuda(CUDA.cuCtxDestroy,
                  [ CUDA.context_t ])


def init_libcupti():
    # Interpose all needed CUPTI functions

    # Events
    register_cupti(CUPTI.cuptiDeviceGetNumEventDomains,
                   [ CUDA.device_t, C.POINTER(C.c_uint32) ])

    register_cupti(CUPTI.cuptiDeviceEnumEventDomains,
                   [ CUDA.device_t, C.POINTER(C.c_size_t), C.POINTER(CUPTI.domain_t) ])

    register_cupti(CUPTI.cuptiDeviceGetEventDomainAttribute,
                   [ CUDA.device_t, CUPTI.domain_t, CUPTI.domain_attr_t, C.POINTER(C.c_size_t), C.c_void_p ])

    register_cupti(CUPTI.cuptiEventDomainGetNumEvents,
                   [ CUPTI.domain_t, C.POINTER(C.c_uint32) ])

    register_cupti(CUPTI.cuptiEventDomainEnumEvents,
                   [ CUPTI.domain_t, C.POINTER(C.c_size_t), C.POINTER(CUPTI.event_t)])

    register_cupti(CUPTI.cuptiEventGetAttribute,
                   [ CUPTI.event_t, CUPTI.event_attr_t, C.POINTER(C.c_size_t), C.c_void_p ])

    register_cupti(CUPTI.cuptiEventGroupSetsCreate,
                   [ CUDA.context_t, C.c_size_t, C.POINTER(CUPTI.event_t), C.c_void_p ])

    register_cupti(CUPTI.cuptiEventGroupSetsDestroy,
                   [ C.POINTER(cupti_group_sets) ])

    register_cupti(CUPTI.cuptiEventGroupGetAttribute,
                   [ C.c_void_p, C.c_int, C.POINTER(C.c_size_t), C.c_void_p ])

    # Metrics
    register_cupti(CUPTI.cuptiDeviceGetNumMetrics,
                   [ CUDA.device_t, C.POINTER(C.c_uint32) ])

    register_cupti(CUPTI.cuptiMetricGetAttribute,
                   [ CUPTI.metric_t, CUPTI.metric_attr_t, C.POINTER(C.c_size_t), C.c_void_p ])

    register_cupti(CUPTI.cuptiDeviceEnumMetrics,
                   [ CUDA.device_t, C.POINTER(C.c_size_t), C.POINTER(CUPTI.metric_t) ])

    register_cupti(CUPTI.cuptiMetricGetNumEvents,
                   [ CUPTI.metric_t, C.POINTER(C.c_uint32) ])

    register_cupti(CUPTI.cuptiMetricEnumEvents,
                   [ CUPTI.metric_t, C.POINTER(C.c_size_t), C.POINTER(CUPTI.event_t) ])

    register_cupti(CUPTI.cuptiMetricGetValue,
                   [ CUDA.device_t,                # device
                     CUPTI.metric_t,               # metric
                     C.c_size_t,                   # eventIdArraySizeBytes
                     C.POINTER(CUPTI.event_t),     # eventIdArray
                     C.c_size_t,                   # eventValueArraySizeBytes
                     C.POINTER(C.c_uint64),        # eventValueArray
                     C.c_uint64,                   # timeDuration
                     C.POINTER(cupti_metric_value) # metricValue
                   ])


def load_libraries():
    global CUDA
    global CUPTI

    try:
        # Load libcuda
        CUDA = C.cdll.LoadLibrary('libcuda.so')

        # Register CUDA types
        CUDA.context_t = C.c_void_p
        CUDA.device_t  = C.c_int
        CUDA.result_t  = C.c_int
    except OSError:
        print 'Could not load library libcuda.so'
        sys.exit(-1)

    try:
        # Load libcupti
        CUPTI = C.cdll.LoadLibrary('libcupti.so')

        # Register CUPTI types
        CUPTI.result_t      = C.c_int

        CUPTI.domain_t      = C.c_uint32
        CUPTI.domain_attr_t = C.c_int

        CUPTI.event_t       = C.c_uint32
        CUPTI.event_attr_t  = C.c_int

        CUPTI.metric_t      = C.c_uint32
        CUPTI.metric_attr_t = C.c_int

        CUPTI.group_set     = cupti_group_set
        CUPTI.group_sets    = cupti_group_sets
        CUPTI.metric_value  = cupti_metric_value

        CUPTI.event_collection_mode = enum(CONTINUOUS = 0,
                                           KERNEL     = 1)

        CUPTI.domain_attr = enum(NAME                 = 0,
                                 INSTANCE_COUNT       = 1,
                                 TOTAL_INSTANCE_COUNT = 3)

        CUPTI.event_attr = enum(NAME              = 0,
                                SHORT_DESCRIPTION = 1,
                                LONG_DESCRIPTION  = 2,
                                CATEGORY          = 3)

        CUPTI.event_group_attr = enum(EVENT_DOMAIN_ID              = 0,
                                      PROFILE_ALL_DOMAIN_INSTANCES = 1,
                                      USER_DATA                    = 2,
                                      NUM_EVENTS                   = 3,
                                      EVENTS                       = 4,
                                      INSTANCE_COUNT               = 5)

        CUPTI.metric_attr = enum(NAME              = 0,
                                 SHORT_DESCRIPTION = 1,
                                 LONG_DESCRIPTION  = 2,
                                 CATEGORY          = 3,
                                 VALUE_KIND        = 4,
                                 EVALUATION_MODE   = 5)

        CUPTI.metric_value_kind = enum(DOUBLE     = 0,
                                       UINT64     = 1,
                                       PERCENT    = 2,
                                       THROUGHPUT = 3)

        CUPTI.metric_evaluation_mode = enum(PER_INSTANCE = 1,
                                            AGGREGATE    = 1 << 1)

    except OSError:
        print 'Could not load library libcupti.so'
        sys.exit(-1)

    # Register functions in the libraries
    init_libcuda()
    init_libcupti()


# Load libraries into memory
load_libraries()


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
