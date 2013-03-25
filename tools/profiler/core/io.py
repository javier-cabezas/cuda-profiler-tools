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

import cPickle
import os
import sys

def get_conf_from_file(counter_file):
    saved_options  = []
    saved_counters = {}

    if counter_file != None:
        if os.path.isfile(counter_file):
            try:
                # Open configuration file
                f_in = open(counter_file, 'r')
            except IOError:
                print 'Error opening file %s' % (counter_file)
                sys.exit(-1)

            try:
                # Load configuration file contents
                saved_options = cPickle.load(f_in)
                saved_counters = cPickle.load(f_in)
                assert isinstance(saved_counters, dict), 'Wrong contents in file %s' % (counter_file)
            except:
                print 'Error wrong contents in file %s' % (counter_file)
                sys.exit(-1)

            # Close configuration file
            f_in.close()
        else:
            print 'Error %s is not a valid file' % (counter_file)
            sys.exit(-1)

    return saved_options, saved_counters


def put_conf_to_file(counter_file, options, counters):
    try:
        f_out = open(counter_file, 'w')
    except IOError:
        print 'Error opening file %s' % (counter_file)
        sys.exit(-1)

    try:
        cPickle.dump(options, f_out)
        cPickle.dump(counters, f_out)
    except:
        print 'Error wrong contents in file %s' % (counter_file)
        sys.exit(-1)

    f_out.close()


# vim:set backspace=2 tabstop=4 shiftwidth=4 textwidth=120 foldmethod=marker expandtab:
