#!/usr/bin/env python
# encoding: utf-8
"""Window class for vimiv."""

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


class Window(Gtk.ApplicationWindow):
    """"Vimiv Window containing the general structure.

    Additionally handles events like fullscreen and resize.

    Attributes:
        app: The main vimiv application to interact with.
        fullscreen: If True, the window is displayed fullscreen.
        last_focused: The last widget that was focused.
        winsize: The windowsize as tuple.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        Gtk.ApplicationWindow.__init__(self)

        self.app = app
        self.is_fullscreen = False
        self.last_focused = ""

        # Configurations from vimivrc
        general = settings["GENERAL"]
        start_fullscreen = general["start_fullscreen"]

        self.connect('destroy', self.app.quit_wrapper)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        # Set initial window size
        try:
            winsize = general["geometry"].split("x")
            self.winsize = (int(winsize[0]), int(winsize[1]))
            self.resize(self.winsize[0], self.winsize[1])
        except:
            self.winsize = (800, 600)
            self.resize(self.winsize[0], self.winsize[1])

        # Fullscreen
        if Gtk.get_minor_version() > 10:
            self.connect_data('window-state-event',
                              Window.on_window_state_change, self)
        else:
            self.connect_object('window-state-event',
                                Window.on_window_state_change, self)
        if start_fullscreen:
            self.toggle_fullscreen()

        # Auto resize
        self.connect("check-resize", self.auto_resize)
        # Focus changes with mouse
        for widget in [self.app["library"].treeview,
                       self.app["thumbnail"].iconview,
                       self.app["manipulate"].scale_bri,
                       self.app["manipulate"].scale_con,
                       self.app["manipulate"].scale_sha,
                       self.app["image"].image]:
            widget.connect("button-release-event", self.focus_on_mouse_click)

    def on_window_state_change(self, event, window=None):
        """Handle fullscreen/unfullscreen correctly.

        Args:
            event: Gtk event that called the function.
            window: Gtk.Window to operate on.
        """
        if window:
            window.is_fullscreen = bool(Gdk.WindowState.FULLSCREEN
                                        & event.new_window_state)
        else:
            self.is_fullscreen = bool(Gdk.WindowState.FULLSCREEN
                                      & event.new_window_state)

    def toggle_fullscreen(self):
        """Toggle fullscreen."""
        if self.is_fullscreen:
            self.unfullscreen()
        else:
            self.fullscreen()

    def auto_resize(self, window):
        """Automatically resize widgets when window is resized.

        Args:
            window: The window which emitted the resize event.
        """
        if self.get_size() != self.winsize:
            self.winsize = self.get_size()
            if self.app.paths:
                if self.app["thumbnail"].toggled:
                    self.app["thumbnail"].calculate_columns()
                if not self.app["image"].user_zoomed:
                    self.app["image"].zoom_to(0)
            self.app["commandline"].info.set_max_width_chars(
                self.winsize[0] / 16)

    def focus_on_mouse_click(self, widget, event_button):
        """Update statusbar with the currently focused widget after mouse click.

        Args:
            widget: The widget that emitted the signal.
            event_button: Mouse button that was pressed.
        """
        self.app["statusbar"].update_info()
