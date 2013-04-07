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

def start(options, counters, metrics, option_conf_file, option_cmd, option_cmd_args, option_out_pattern):
    # Collect enabled options
    enabled_options = [ option for option in options if option.active == True ]

    # Collect enabled events
    enabled_counters = [ counter for domain, _counters in counters.items()
                                 for counter in _counters if counter.active == True ]

    # Collect enabled metrics
    enabled_metrics = [ metric for category, _metrics in metrics.items()
                               for metric in _metrics if metric.active == True ]

    # Enable counters needed by the metrics
    for metric in enabled_metrics:
        for counter_name in metric.counters:
            enabled_counter = [ counter for counter in enabled_counters if counter.name == counter_name ]
            
            if len(enabled_counter) == 0:
                # Not enabled by default
                counter = [ counter for domain, _counters in counters.items()
                                    for counter in _counters if counter.name == counter_name ]
                assert len(counter) > 0, "Counter name not known"

                enabled_counters += counter
            
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
                         enabled_metrics,
                         progress,
                         out_pattern = option_out_pattern)


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
