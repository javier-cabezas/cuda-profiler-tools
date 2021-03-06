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

import copy
import os
from gi.repository import Gtk
from gi.repository import Gdk

from cudaprof.common import now
import cudaprof.cuda   as _cuda
import cudaprof.io     as _io
import cudaprof.runner as _runner

class NotebookDomains(Gtk.Notebook):
    def __init__(self, options, domains, metrics, parent):
        Gtk.Notebook.__init__(self)

        self.parent = parent

        self.checkboxes_opts = {}
        self.checkboxes = {}

        # Add frame for the options
        frame_opts = Gtk.Frame()
        layout = Gtk.ScrolledWindow()

        grid_options = Gtk.VBox()

        layout.add_with_viewport(grid_options)
        frame_opts.add(layout)

        for option in options:
            # Create one checkbox per option
            check_counter = Gtk.CheckButton(option.name)
            check_counter.connect("toggled", self.on_option_toggled, option)
            check_counter.set_active(option.active)
            check_counter.set_tooltip_text(option.description)
            grid_options.add(check_counter)

            self.checkboxes_opts[option.name] = check_counter

        self.append_page(frame_opts, Gtk.Label('Options'))
        frame_opts.show()

        all_domains = sorted(set(domains.keys() + metrics.keys()))

        # Create one page per domain
        for domain in all_domains:
            grid_frames = Gtk.VBox()

            if domain in metrics.keys():
                frame_metrics  = Gtk.Expander()
                frame_metrics.set_expanded(True)
                frame_metrics.set_label('Metrics')

                grid_metrics = Gtk.VBox()

                for metric in sorted(metrics[domain], key = lambda x: x.name):
                    # Create one checkbox per counter
                    check_metric = Gtk.CheckButton(metric.name)
                    check_metric.connect("toggled", self.on_checkbox_toggled, metric)
                    check_metric.set_active(metric.active)
                    check_metric.set_tooltip_text(metric.description)
                    grid_metrics.add(check_metric)

                    self.checkboxes[metric.name] = check_metric

                frame_metrics.add(grid_metrics)
                grid_frames.pack_start(frame_metrics, False, False, 0)

            if domain in domains.keys():
                expander_counters  = Gtk.Expander()
                expander_counters.set_expanded(True)
                expander_counters.set_label('Counters')

                grid_counters = Gtk.VBox()

                for counter in sorted(domains[domain], key = lambda x: x.name):
                    # Create one checkbox per counter
                    check_counter = Gtk.CheckButton(counter.name)
                    check_counter.connect("toggled", self.on_checkbox_toggled, counter)
                    check_counter.set_active(counter.active)
                    check_counter.set_tooltip_text(counter.description)
                    grid_counters.add(check_counter)

                    self.checkboxes[counter.name] = check_counter

                expander_counters.add(grid_counters)
                grid_frames.pack_start(expander_counters, False, False, 0)

            layout = Gtk.ScrolledWindow()
            layout.add_with_viewport(grid_frames)

            self.append_page(layout, Gtk.Label(domain))


    def on_option_toggled(self, check_option, *data):
        assert len(data) == 1
        option = data[0]
        option.set_active(check_option.get_active())


    def on_checkbox_toggled(self, check_counter, *data):
        assert len(data) == 1
        counter = data[0]
        counter.set_active(check_counter.get_active())

    def update_conf(self, options, counters):
        for option in options:
            self.checkboxes_opts[option.name].connect("toggled",
                                                      self.on_option_toggled, option)
            self.checkboxes_opts[option.name].set_active(option.active)

        for ctrs in counters.values():
            for counter in ctrs:
                self.checkboxes[counter.name].connect("toggled",
                                                      self.on_checkbox_toggled, counter)
                self.checkboxes[counter.name].set_active(counter.active)


def get_abspath(path):
    path_nouser = os.path.expanduser(path)
    path_novars = os.path.expanduser(path_nouser)
    return os.path.abspath(path_novars)


class MainWindow(Gtk.Window):
    def __init__(self, options, domains, metrics, conf_file, cmd, args, out_pattern):
        Gtk.Window.__init__(self, title="CUDA Profiler Configuration Tool")
        self.options = copy.deepcopy(options)
        self.domains = copy.deepcopy(domains)
        self.metrics = copy.deepcopy(metrics)

        self.initialized = False

        if conf_file != None:
            self.current_conf_in  = get_abspath(conf_file)
            self.current_conf_out = get_abspath(conf_file)
        else:
            self.current_conf_in  = None
            self.current_conf_out = None

        self.current_cmd         = get_abspath(cmd)
        self.current_out_pattern = get_abspath(out_pattern)

        # Add box
        self.box = Gtk.VBox()
        self.add(self.box)

        # Add notebook with the counters
        self.notebook_domains = NotebookDomains(self.options, self.domains, self.metrics, self)
        self.box.pack_start(self.notebook_domains, True, True, 0)

        self.notebook_domains.set_size_request(-1, 300)

        # Add boxes for buttons
        self.box_load = Gtk.HBox()
        self.box.pack_start(self.box_load, False, False, 0)

        self.box_save = Gtk.HBox()
        self.box.pack_start(self.box_save, False, False, 0)

        self.box_cmdline = Gtk.VBox()

        self.box_cmd = Gtk.HBox()
        self.box_cmdline.pack_start(self.box_cmd, False, False, 0)
        self.box_args = Gtk.HBox()
        self.box_cmdline.pack_start(self.box_args, False, False, 0)
        self.box_out_pattern = Gtk.HBox()
        self.box_cmdline.pack_start(self.box_out_pattern, False, False, 0)

        self.box.pack_start(self.box_cmdline, False, False, 0)

        self.box_profile = Gtk.HBox()
        self.box.pack_start(self.box_profile, False, False, 0)

        self.box_log = Gtk.HBox()
        self.box.pack_start(self.box_log, False, False, 0)

        ##
        ## CONFIGURATION LOAD/SAVE
        ##

        # Add save button and entry for filename
        self.entry_conf_in = Gtk.Entry()
        self.entry_conf_out = Gtk.Entry()

        image_load = Gtk.Image()
        image_load.set_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.BUTTON)
        image_save = Gtk.Image()
        image_save.set_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.BUTTON)

        self.button_load_choose = Gtk.Button()
        self.button_load_choose.set_image(image_load)

        self.button_save_choose = Gtk.Button()
        self.button_save_choose.set_image(image_save)

        self.button_load = Gtk.Button('Load')
        self.button_save = Gtk.Button('Save')

        if self.current_conf_in == None:
            self.button_load.set_sensitive(False)

        if self.current_conf_out == None:
            self.button_save.set_sensitive(False)

        self.box_load.pack_start(self.entry_conf_in, True, True, 0)
        self.box_load.pack_start(self.button_load_choose, False, False, 0)
        self.box_load.pack_start(self.button_load, False, False, 0)

        self.box_save.pack_start(self.entry_conf_out, True, True, 0)
        self.box_save.pack_start(self.button_save_choose, False, False, 0)
        self.box_save.pack_start(self.button_save, False, False, 0)

        ##
        ## PROFILE
        ##

        # Add profile button
        self.button_profile = Gtk.Button('Profile')
        self.button_profile.connect("clicked", self.on_profile_clicked)
        # Add cmd entry
        self.label_cmd  = Gtk.Label('Command')
        self.label_cmd.set_justify(Gtk.Justification.LEFT)
        self.label_args = Gtk.Label('Arguments')
        self.label_args.set_justify(Gtk.Justification.LEFT)
        self.label_out_pattern = Gtk.Label('Output files')
        self.label_out_pattern.set_justify(Gtk.Justification.LEFT)

        self.entry_cmd = Gtk.Entry()
        self.entry_args = Gtk.Entry()
        self.entry_args.set_text(args)
        self.entry_out_pattern = Gtk.Entry()

        # Add cmd and args to the box
        self.box_cmd.pack_start(self.label_cmd, False, False, 0)
        self.box_cmd.pack_end(self.entry_cmd, True, True, 0)
        self.box_args.pack_start(self.label_args, False, False, 0)
        self.box_args.pack_end(self.entry_args, True, True, 0)
        self.box_out_pattern.pack_start(self.label_out_pattern, False, False, 0)
        self.box_out_pattern.pack_end(self.entry_out_pattern, True, True, 0)

        self.box_profile.pack_end(self.button_profile, False, False, 0)

        homedir = os.path.expanduser("~")

        if conf_file != None:
            path_in = self.current_conf_in.replace(homedir, '~')
            self.entry_conf_in.set_text(path_in)
            path_out = self.current_conf_out.replace(homedir, '~')
            self.entry_conf_out.set_text(path_out)
        else:
            path = os.getcwd() + '/'
            path = path.replace(homedir, '~')
            self.entry_conf_in.set_text(path)
            self.entry_conf_out.set_text(path)

        path_cmd = self.current_cmd.replace(homedir, '~')
        self.entry_cmd.set_text(path_cmd)
        path_out_pattern = self.current_out_pattern.replace(homedir, '~')
        self.entry_out_pattern.set_text(path_out_pattern)

        self.button_profile.set_sensitive(os.path.isfile(self.current_cmd))

        ##
        ## LOG
        ##
        self.expander_log = Gtk.Expander()
        self.expander_log.set_label('Log')
        self.expander_log.set_resize_toplevel(True)

        self.label_log = Gtk.TextView()
        self.label_log.set_editable(False)

        self.layout_log = Gtk.ScrolledWindow()
        self.layout_log.add(self.label_log)

        self.expander_log.add(self.layout_log)

        self.box_log.pack_end(self.expander_log, True, True, 0)

        # Set button/label sizes
        self.label_cmd.set_size_request(100, -1)
        self.label_args.set_size_request(100, -1)
        self.label_out_pattern.set_size_request(100, -1)

        self.button_load.set_size_request(100, -1)
        self.button_save.set_size_request(100, -1)
        self.button_profile.set_size_request(100, -1)

        self.layout_log.set_size_request(-1, 200)

        # Connect signals
        self.button_load.connect("clicked", self.on_load_clicked)
        self.button_save.connect("clicked", self.on_save_clicked)

        self.button_load_choose.connect("clicked", self.on_choose_load_clicked)
        self.button_save_choose.connect("clicked", self.on_choose_save_clicked)

        self.entry_conf_in.connect("changed", self.on_path_in_changed)
        self.entry_conf_out.connect("changed", self.on_path_out_changed)

        self.entry_out_pattern.connect("changed", self.on_out_pattern_changed)

        self.entry_cmd.connect("changed", self.on_path_cmd_changed)

        hints = Gdk.Geometry()
        hints.min_height = -1  # Current minimum size
        hints.min_width  = 500

        self.set_geometry_hints(self, hints, Gdk.WindowHints.MIN_SIZE)

        self.initialized = True

    def on_path_in_changed(self, entry):
        path = entry.get_text()

        self.current_conf_in = get_abspath(path)
        self.button_load.set_sensitive(os.path.isfile(self.current_conf_in))

    def on_path_out_changed(self, entry):
        path = entry.get_text()

        self.current_conf_out = get_abspath(path)
        dirname = os.path.dirname(self.current_conf_out)

        is_dir = False
        try:
            is_dir = os.path.samefile(dirname,
                                      self.current_conf_out) or os.path.isdir(self.current_conf_out)
        except OSError:
            # Ignore
            pass

        self.button_save.set_sensitive(not is_dir and os.path.isdir(dirname))

    def on_path_cmd_changed(self, entry):
        path = entry.get_text()

        self.current_cmd = get_abspath(path)

        self.button_profile.set_sensitive(os.path.isfile(self.current_cmd))

    def on_out_pattern_changed(self, entry):
        path = entry.get_text()

        self.current_out_pattern = get_abspath(path)
        dirname = os.path.dirname(self.current_out_pattern)

        is_dir = (path[-1] == '/')

        self.button_profile.set_sensitive((not is_dir) and
                                          os.path.isdir(dirname) and
                                          _cuda.is_valid_output_pattern(self.current_out_pattern))

    def on_choose_load_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,   Gtk.ResponseType.OK))

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_conf_in = dialog.get_filename()
            self.entry_conf_in.set_text(dialog.get_filename())
            self.button_load.set_sensitive(True)
        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

    def on_choose_save_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,   Gtk.ResponseType.OK))

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_conf_out = dialog.get_filename()
            self.entry_conf_out.set_text(dialog.get_filename())
            self.button_save.set_sensitive(True)
        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

    def on_load_clicked(self, button):
        # Create counters
        self.options = _cuda.get_options()
        # Reset counters
        self.domains = _cuda.get_counters(False)
        # Load from file
        options_file, counters_file = _io.get_conf_from_file(self.current_conf_in)

        # Merge options from file
        cudaprof.init_options(self.options, options_file)
        # Merge counters from file
        cudaprof.init_counters(self.domains, counters_file)
        # Update checkboxes with the new values
        self.notebook_domains.update_conf(self.options, self.domains)

        buf = self.label_log.get_buffer()
        buf.insert(buf.get_start_iter(),
                   "%s> Loaded configuration file '%s'\n" %
                   (now(),
                    self.current_conf_in))


    def on_save_clicked(self, button):
        # Write to file
        _io.put_conf_to_file(self.current_conf_out, self.options, self.domains, self.metrics)

        buf = self.label_log.get_buffer()
        buf.insert(buf.get_start_iter(),
                   "%s> Saved configuration file '%s'\n" %
                   (now(),
                    self.current_conf_out))


    def on_profile_clicked(self, button):
        # Collect enabled options
        enabled_options = [ option for option in self.options if option.active == True ]
        # Collect enabled events
        enabled_counters = [ counter for counters in self.domains.values()
                                     for counter in counters if counter.active == True ]

        # Collect enabled metrics
        enabled_metrics = [ metric for metrics in self.metrics.values()
                                   for metric in metrics if metric.active == True ]

        # Enable counters needed by the metrics
        for metric in enabled_metrics:
            for counter_name in metric.counters:
                enabled_counter = [ counter for counter in enabled_counters if counter.name == counter_name ]

                if len(enabled_counter) == 0:
                    # Not enabled by default
                    counter = [ counter for counters in self.domains.values()
                                        for counter in counters if counter.name == counter_name ]
                    assert len(counter) > 0, "Counter name not known"

                    enabled_counters += counter

        cmd  = self.entry_cmd.get_text()
        args = self.entry_args.get_text()

        groups = _cuda.get_event_groups(enabled_counters)
        buf = self.label_log.get_buffer()
        buf.insert(buf.get_start_iter(), "%s> BEGIN PROFILE: Command: '%s %s'\n" % (now(), cmd, args))

        # Repaint
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Generator to update the GUI on each execution
        def print_progress(n):
            i = 1
            while i <= n:
                buf.insert(buf.get_start_iter(), "%s> Run %d/%d\n" % (now(), i, n))
                # Update GUI since we are in a handler
                while Gtk.events_pending():
                    Gtk.main_iteration()

                i +=1
                yield

        progress = print_progress(len(groups))

        _runner.launch_groups(self.current_cmd, args, enabled_options, groups,
                              self.metrics, progress, out_pattern = self.current_out_pattern)

        buf.insert(buf.get_start_iter(), "%s> END PROFILE\n" % now())


def start(options, counters, metrics, option_conf_file, option_cmd, option_cmd_args, option_out_pattern, option_deps_only):
    # Create window
    win = MainWindow(options, counters, metrics, option_conf_file, option_cmd, option_cmd_args, option_out_pattern)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()

    # Run!
    Gtk.main()

