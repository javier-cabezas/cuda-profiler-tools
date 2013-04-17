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

from datetime import datetime

def now():
    time = datetime.time(datetime.now())
    return time.strftime("%H:%M:%S")

def enum(**enums):
    return type('Enum', (), enums)

class Option:
    def __init__(self, name, description, value = None):
        self.name        = name
        self.description = description
        self.value       = value

        self.active = False

    def __repr__(self):
        if self.value != None:
            return '%s=%s' % (self.name, self.value)
        else:
            return '%s' % (self.name)

    def set_active(self, active):
        self.active = active


class Domain(dict):
    def __init__(self, name, id, i_profiled, i_total):
        self.name       = name
        self.id         = id
        self.i_profiled = i_profiled
        self.i_total    = i_total


class Counter(object):
    CATEGORIES = {
                   0: 'Instruction',
                   1: 'Memory',
                   2: 'Cache',
                   3: 'Profile trigger'
                 }

    def __init__(self, name, description, category, id, domain):
        self.name        = name
        self.description = description
        self.category    = category
        self.id          = id
        self.domain      = domain

        self.active = False

    def __repr__(self):
        ret = 'Counter: %s' % (self.name)
        return ret

    def set_active(self, active):
        self.active = active

    def is_internal(self):
        return self.name[0:2] == '__'


class Metric(object):
    CATEGORIES = {
                    0: 'Memory',
                    1: 'Instruction',
                    2: 'Multiprocessor',
                    3: 'Cache',
                    4: 'Texture',
                 }

    def __init__(self, name, description, category, id, value_kind,
                 evaluation_instance, evaluation_aggregate, counters):
        self.name        = name
        self.description = description
        self.category    = category
        self.id          = id
        self.value_kind  = value_kind
        self.eval_instance  = evaluation_instance
        self.eval_aggregate = evaluation_aggregate
        self.counters    = counters

        self.active = False

    def __repr__(self):
        ret = 'Metric: %s' % (self.name)
        return ret

    def set_active(self, active):
        self.active = active

    def is_internal(self):
        return self.name[0:2] == '__'


