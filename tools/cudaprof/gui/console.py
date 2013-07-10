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

from cudaprof.common import now
import cudaprof.cuda   as cuda
import cudaprof.runner as runner

def start(options, counters, metrics, option_conf_file, option_cmd, option_cmd_args, option_out_pattern, option_deps_only):
    # Collect enabled options
    enabled_options = [ option for option in options if option.active == True ]

    # Collect enabled events
    enabled_counters = [ counter for _counters in counters.values()
                                 for counter in _counters if counter.active == True ]

    # Collect enabled metrics
    enabled_metrics = [ metric for _metrics in metrics.values()
                               for metric in _metrics if metric.active == True ]

    # Enable counters needed by the metrics
    for metric in enabled_metrics:
        for metric_counter in metric.counters:
            enabled_counter = [ counter for counter in enabled_counters if counter.name == metric_counter.name ]

            if len(enabled_counter) == 0:
                # Not enabled by default
                counter = [ counter for _counters in counters.values()
                                    for counter in _counters if counter.name == metric_counter.name ]
                assert len(counter) > 0, "Counter name not known"

                enabled_counters += counter

    groups = cuda.get_event_groups(enabled_counters)

    if option_deps_only:
        for group in groups:
            print ','.join([ counter.name for counter in group ])

        return

    def print_progress(n):
        i = 1
        while i <= n:
            print "%s> Run %d/%d" % (now(), i, n)
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
