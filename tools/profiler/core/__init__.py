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
    for option_saved in options_saved:
        assert isinstance(option_saved, Option), 'Wrong contents in list'

        option = [ option for option in options_new if option.name == option_saved.name ]
        if len(option) == 1:
            option[0].set_active(option_saved.active)


def init_counters(counters_new, counters_saved):
    # Initialize counter values with the ones stored in the file (if any)
    for domain, counters in counters_saved.items():
        assert isinstance(counters, list), 'Wrong contents in dict'

        # Only merge those counters found in both dictionaries
        if domain in counters_new.keys():
            my_counters = counters_new[domain]

            for saved in counters:
                assert isinstance(saved, Counter), 'Wrong contents in dict'

                counter = [ counter for counter in my_counters if counter.name == saved.name ]
                if len(counter) == 1:
                    counter = counter[0]
                    counter.set_active(saved.active)


def print_counters(tag, counters):
    print tag
    for domain, ctrs in counters.items():
        for counter in ctrs: 
            if counter.active == True:
                print counter


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
