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

import glob
import os
import sys
import subprocess as proc
import tempfile

import shutil

import cudaprof.cuda as cuda

def _get_elem(f, container):
    for elem in container:
        if f(elem) == True:
            return elem

    return None

def merge_files(output, input_files):
    columns = []

    files_data = {}
    column_to_file_map = {}

    data = {}
    nlines = 0

    # Iterate per input file
    for _f in input_files:
        f = open(_f, 'r')
        file_columns = []

        lines_data = []

        # Parse all lines
        for line in f.readlines():
            line = line[:-1]
            if line[0] == '#':
                continue

            # Read colum names
            if len(file_columns) == 0:
                file_columns = line.split(',')

                # Find new columns
                for i, column in zip(range(len(file_columns)), file_columns):
                    if column not in columns:
                        column_to_file_map[column] = (_f, i)
                        columns.append(column)

            else: # Read colum data
                line_data = line.split(',')

                if len(line_data) < len(file_columns):
                    line_data += [''] * (len(file_columns) - len(line_data))

                lines_data.append(line_data)

        files_data[_f] = lines_data

        if nlines == 0:
            nlines = len(lines_data)
        else:
            assert nlines == len(lines_data), 'Corrupted data'

    # Merge results for each line
    for i in range(nlines):
        for column in columns:
            f, c = column_to_file_map[column]
            #out_data.append(files_data[f][i][c])

            if not data.has_key(column):
                data[column] = list()

            data[column].append(files_data[f][i][c])

    return columns, data, nlines


def launch_group(cmd, args, options, group, **kwargs):
    csv      = kwargs.get('csv', True)
    out_dir  = kwargs.get('out_dir', './')
    out_file = out_dir + '/cuda_profile_%p_%d.log'

    lines = len(options) + len(group)

    if lines > 0:
        # Fill config file
        _f, f_name = tempfile.mkstemp(text = True)

        f = os.fdopen(_f, 'w')

        for option in options:
            f.write('%s\n' % option)

        for counter in group:
            f.write('%s\n' % counter.name)

        f.close()

        os.environ['COMPUTE_PROFILE_CONFIG'] = f_name

    # Modify the environment
    os.environ['COMPUTE_PROFILE']     = '1'
    os.environ['COMPUTE_PROFILE_CSV'] = '%d' % csv
    os.environ['COMPUTE_PROFILE_LOG'] = out_file

    # Execute the program
    p = proc.Popen([cmd] + args.split(' '),
                   stdout = proc.PIPE,
                   stderr = proc.PIPE,
                   env = os.environ)
    pid = p.pid
    p.wait()

    if lines > 0:
        # Remove temporary file
        try:
            os.remove(f_name)
        except OSError:
            print 'Error removing temporary file for conf "%s"' % f_name

    return pid

def launch_groups(cmd, args, options, groups, metrics, progress = None, **kwargs):
    assert len(groups) > 0, 'Empty counter group'

    aggregate_mode = _get_elem(lambda opt: opt.name == 'countermodeaggregate',
                               options) != None

    #counters = []
    #for group in groups:
    #    counters += group

    csv              = kwargs.get('csv', True)
    out_file_pattern = kwargs.get('out_pattern', 'cuda_profile_%d.log')

    pid = os.getpid()

    # Create temporary output directory
    tempdir = tempfile.gettempdir() + ('/cuda-profiler-tools.%d' % pid)

    if not os.path.isdir(tempdir):
        try:
            os.mkdir(tempdir)
        except OSError:
            print 'Error creating tmp dir: %s' % tempdir
            sys.exit(-1)

    group_pids = []

    for group in groups:
        # Report progress
        if progress != None:
            progress.next()

        group_pid = launch_group(cmd, args, options, group, csv = csv, out_dir = tempdir)
        group_pids.append(group_pid)

    gpus = len(glob.glob(tempdir + '/cuda_profile_%d_*.log' % group_pids[0]))

    for gpu in range(gpus):
        files = []
        for group_pid in group_pids:
            files.append(tempdir + '/cuda_profile_%d_%d.log' % (group_pid, gpu))

        columns, data, nlines = merge_files(out_file_pattern % gpu, files)

        if len(metrics) > 0:
            metrics_values = cuda.compute_metrics(gpu,
                                                  metrics,
                                                  columns,
                                                  data,
                                                  nlines,
                                                  aggregate_mode)

        f = open(out_file_pattern % gpu, 'w')

        f.write(','.join(columns) + '\n')

        for line in range(nlines):
            row = []
            for k in columns:
                row.append(data[k][line])

            f.write(','.join(row) + '\n')

        f.close()

    # Remove temporary output directory
    shutil.rmtree(tempdir)

# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
