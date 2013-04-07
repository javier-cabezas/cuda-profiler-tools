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

import common
import cuda
import io
import runner

Option =  common.Option
Counter = common.Counter

def init_options(options_new, options_saved):
    assert isinstance(options_saved, list), 'Wrong contents in options'

    # Initialize on values with the ones stored in the file (if any)
    for option_new in options_new:
        option_saved = [ option for option in options_saved if option.name == option_new.name ]
        if len(option_saved) == 1:
            option_new.set_active(option_saved[0].active)


def init_counters(counters_new, counters_saved):
    # Initialize counter values with the ones stored in the file (if any)
    for domain, counters in counters_new.items():
        # Only merge those counters found in both dictionaries
        for counter_new in counters:
            counter_saved = [ counter for counter in counters_saved if counter.name == counter_new.name ]
            if len(counter_saved) == 1:
                counter_new.set_active(counter_saved[0].active)


def init_metrics(metrics_new, metrics_saved):
    # Initialize metric values with the ones stored in the file (if any)
    for category, metrics in metrics_new.items():
        # Only merge those metrics found in both dictionaries
        for metric_new in metrics:
            metric_saved = [ metric for metric in metrics_saved if metric.name == metric_new.name ]
            if len(metric_saved) == 1:
                metric_new.set_active(metric_saved[0].active)



def print_counters(tag, counters):
    print tag
    for domain, ctrs in counters.items():
        for counter in ctrs: 
            if counter.active == True:
                print counter


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
