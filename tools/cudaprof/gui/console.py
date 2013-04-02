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

import cudaprof.common as common
import cudaprof.cuda   as cuda
import cudaprof.runner as runner

def start(options, counters, option_conf_file, option_cmd, option_cmd_args, option_out_file):
    # Collect enabled options
    enabled_options = [ option for option in options if option.active == True ]
    # Collect enabled events
    enabled_counters = [ counter for domain, _counters in counters.items()
                                 for counter in _counters if counter.active == True ]

    groups = cuda.get_event_groups(enabled_counters)

    def print_progress(n):
        i = 1
        while i <= n:
            print "%s> Run %d/%d" % (common.now(), i, n)
            i +=1
            yield

    progress = print_progress(len(groups))

    runner.launch_groups(option_cmd,
                         option_cmd_args,
                         enabled_options,
                         groups,
                         progress,
                         out_file = option_out_file)


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
