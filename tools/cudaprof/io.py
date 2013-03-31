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

import os
import sys

import ConfigParser

class OptionDescr:
    def __init__(self, name, active):
        self.name    = name
        self.active = active

class CounterDescr:
    def __init__(self, name, active):
        self.name    = name
        self.active = active

def get_conf_from_file(counter_file):
    saved_options  = []
    saved_counters = []

    if counter_file == None:
        return saved_options, saved_counters

    config = ConfigParser.RawConfigParser()
    config.read(counter_file)

    for option, active in config.items('Options'):
        saved_options.append(OptionDescr(option, bool(int(active))))
    
    for counter, active in config.items('Counters'):
        saved_counters.append(CounterDescr(counter, bool(int(active))))

    return saved_options, saved_counters


def put_conf_to_file(counter_file, options, domains):
    config = ConfigParser.RawConfigParser()

    config.add_section('Options')

    for option in options:
        config.set('Options', option.name, '%d' % option.active)

    config.add_section('Counters')

    for name, counters in domains.items():
        for counter in counters:
            config.set('Counters', counter.name, '%d' % counter.active)

    try:
        f_out = open(counter_file, 'wb')
    except IOError:
        print 'Error opening file %s' % (counter_file)
        sys.exit(-1)

    config.write(f_out)

    f_out.close()


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
