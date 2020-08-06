from pathlib import Path
from logging import getLogger

import gi
import cairo

from .namespace import Namespace
from .mappers import RatioCoordinatesMapper
from .xrandr import parse_xrandr, calculate_virtual_space

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk  # noqa: E402

gi.require_version('Gio', '2.0')
from gi.repository import Gio  # noqa: E402


log = getLogger(__name__)


def system_font():
    try:
        settings = Gio.Settings(schema='org.gnome.desktop.interface')
        # Other options: 'document-font-name', 'monospace-font-name'
        fontdesc = settings.get_string('font-name')

    except Exception:

        settings = Gtk.Settings.get_default()
        fontdesc = settings.get_property('gtk-font-name')

    font, size = fontdesc.rsplit(' ', 1)
    log.info('System font set to {} with size {}'.format(repr(font), size))
    return font.strip(), int(size)


def color(hexstr):
    color = Gdk.RGBA()
    color.parse(hexstr)

    return (
        color.red,
        color.green,
        color.blue,
    )


SYSTEM_FONT_NAME, SYSTEM_FONT_SIZE = system_font()
STYLE = Namespace({
    'display': {
        'padding': (3, 3, 3, 3),
        'primary': {
            'color': color('#111111'),
            'padding': (5, 5, 0, 5),
            'proportion': 0.10,
        },
        'background': {
            'selected': color('#15539e'),
            'unselected': color('#353535'),
            'assigned': color('#ff7d01'),
            'both': color('#ffa600'),
        },
        'border': {
            'line_width': 1,
            'color': color('#1b1b1b'),
        },
        'name': {
            'font': SYSTEM_FONT_NAME,
            'size': SYSTEM_FONT_SIZE + 2,
            'color': color('#ffffff'),
        },
        'resolution': {
            'font': SYSTEM_FONT_NAME,
            'size': SYSTEM_FONT_SIZE,
            'color': color('#cccccc'),
        },
    },
    'canvas': {
        'padding': (20, 20, 20, 20),
        'background': color('#2d2d2d'),
    },
})


class MyApp(object):
    """Double buffer in PyGObject with cairo"""

    def __init__(self, displays):

        # Get screens
        self.displays = displays
        self.selected = None
        self.assigned = []
        self.mapper = None

        # Build GUI
        self.here = Path(__file__).resolve().parent
        self.ui = self.here / 'displays.glade'

        self.builder = Gtk.Builder()
        self.builder.add_from_file(str(self.ui))

        # Get objects
        go = self.builder.get_object
        self.window = go('window')

        self.drawing = go('drawing')
        self.drawing.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK,
        )

        # Create buffer
        self.double_buffer = None

        # Connect signals
        self.builder.connect_signals(self)

        # Everything is ready
        self.window.show()

        # Identify all displays
        # self._identifiers = []
        # self.identify_displays()

    def identify_displays(self):

        for name, display in self.displays.items():

            x_offset = display['x_offset']
            y_offset = display['y_offset']
            width = display['width']
            height = display['height']

            label = Gtk.Label()
            label.set_markup('<big>{}</big>'.format(name))

            window = Gtk.Window(title=name)
            window.set_skip_taskbar_hint(True)
            window.set_skip_pager_hint(True)
            window.set_accept_focus(False)
            window.set_keep_above(True)
            window.set_decorated(False)
            window.set_deletable(False)

            window.add(label)
            window.move(
                x_offset + width * 0.05,
                y_offset + height * 0.10,
            )
            window.show_all()

            self._identifiers.append(window)

    def _map_display(self, display):
        if self.mapper is None:
            raise RuntimeError('Invalid coordinates mapper')

        # Fetch display variables
        x_offset = display['x_offset']
        y_offset = display['y_offset']
        width = display['width']
        height = display['height']

        # Get display location in canvas
        top_left_x, top_left_y = self.mapper.map(
            x_offset,
            y_offset,
        )

        bottom_right_x, bottom_right_y = self.mapper.map(
            x_offset + width,
            y_offset + height,
        )

        # Apply padding
        top, right, bottom, left = STYLE.display.padding
        return (
            (
                top_left_x + left,
                top_left_y + top,
            ), (
                bottom_right_x - right,
                bottom_right_y - bottom
            ),
        )

    def draw_displays(self):
        """
        Draw something into the buffer.
        """

        db = self.double_buffer
        if db is None:
            raise RuntimeError('Invalid double buffer')

        # Create cairo context with double buffer as its destination
        cc = cairo.Context(db)

        # Determine the virtual space
        vspace_w, vspace_h = calculate_virtual_space(self.displays)

        # Compute scaling
        widget_w, widget_h = db.get_width(), db.get_height()

        self.mapper = RatioCoordinatesMapper(
            (vspace_w, vspace_h),
            (widget_w, widget_h),
            padding=STYLE.canvas.padding,
        )

        # Draw the canvas background
        cc.set_source_rgb(*STYLE.canvas.background)
        cc.paint()

        for name, display in self.displays.items():
            (
                top_left_x,
                top_left_y,
            ), (
                bottom_right_x,
                bottom_right_y,
            ) = self._map_display(display)

            to_x, to_y, to_width, to_height = (
                top_left_x,
                top_left_y,
                bottom_right_x - top_left_x,
                bottom_right_y - top_left_y,
            )

            # Draw display background
            color = STYLE.display.background.unselected
            if name == self.selected and name in self.assigned:
                color = STYLE.display.background.both
            elif name in self.assigned:
                color = STYLE.display.background.assigned
            elif name == self.selected:
                color = STYLE.display.background.selected

            cc.set_line_width(0)
            cc.set_source_rgb(*color)
            cc.rectangle(
                to_x,
                to_y,
                to_width,
                to_height,
            )
            cc.fill_preserve()

            # Draw display border
            cc.set_line_width(STYLE.display.border.line_width)
            cc.set_source_rgb(*STYLE.display.border.color)
            cc.stroke()

            # Draw bar if primary
            if display['primary']:
                top, right, bottom, left = STYLE.display.primary.padding
                proportion = STYLE.display.primary.proportion

                cc.set_line_width(0)
                cc.set_source_rgb(*STYLE.display.primary.color)
                cc.rectangle(
                    to_x + left,
                    to_y + top,
                    to_width - left - right,
                    to_height * proportion - bottom,
                )
                cc.fill()

            # Draw display name
            cc.select_font_face(
                STYLE.display.name.font,
                cairo.FontSlant.NORMAL,
                cairo.FontWeight.NORMAL,
            )
            cc.set_font_size(STYLE.display.name.size)
            cc.set_source_rgb(*STYLE.display.name.color)

            center_x, center_y = (
                to_x + (to_width / 2),
                to_y + (to_height / 2),
            )

            name_dimensions = cc.text_extents(name)
            cc.move_to(
                center_x - name_dimensions.width / 2,
                center_y + name_dimensions.height / 2,
            )
            cc.show_text(name)

            # Draw screen resolution
            cc.select_font_face(
                STYLE.display.resolution.font,
                cairo.FontSlant.NORMAL,
                cairo.FontWeight.NORMAL,
            )
            cc.set_font_size(STYLE.display.resolution.size)
            cc.set_source_rgb(*STYLE.display.resolution.color)

            resolution = '{} x {}'.format(
                display['width'],
                display['height'],
            )
            resolution_dimensions = cc.text_extents(resolution)
            cc.move_to(
                center_x - resolution_dimensions.width / 2,
                center_y + resolution_dimensions.height / 2 + (
                    name_dimensions.height + STYLE.display.name.size // 2
                ),
            )
            cc.show_text(resolution)

        # Flush drawing actions
        db.flush()

    def on_draw_cb(self, widget, cr):
        """
        Throw double buffer into widget drawable.
        """

        if self.double_buffer is None:
            raise RuntimeError('Invalid double buffer')

        cr.set_source_surface(self.double_buffer, 0, 0)
        cr.paint()

        return False

    def on_configure_cb(self, widget, event, data=None):
        """
        Configure the double buffer based on size of the widget.
        """

        # Destroy previous buffer
        if self.double_buffer is not None:
            self.double_buffer.finish()
            self.double_buffer = None

        # Create a new buffer
        self.double_buffer = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            widget.get_allocated_width(),
            widget.get_allocated_height(),
        )
        log.debug(
            'Double buffer {}x{} allocated'.format(
                widget.get_allocated_width(),
                widget.get_allocated_height(),
            )
        )

        # Initialize the buffer
        self.draw_displays()

        return False

    def motion_cb(self, widget, event):
        if self.mapper is None:
            raise RuntimeError('Invalid coordinates mapper')

        selected = None
        for name, display in self.displays.items():

            (
                top_left_x,
                top_left_y,
            ), (
                bottom_right_x,
                bottom_right_y,
            ) = self._map_display(display)

            if (
                event.x >= top_left_x and
                event.x <= bottom_right_x and
                event.y >= top_left_y and
                event.y <= bottom_right_y
            ):
                selected = name
                break

        if selected != self.selected:
            log.debug('Selected: {}'.format(selected))

            self.selected = selected
            self.draw_displays()
            self.drawing.queue_draw()

    def click_cb(self, widget, event):

        # Ignore non right clicks and clicks not in the screens
        if event.button != 1 or self.selected is None:
            return

        # Unassign previous display
        if self.selected in self.assigned:
            self.assigned.remove(self.selected)

        # If not, assign the currently selected display
        else:
            self.assigned.append(self.selected)

        self.draw_displays()
        self.drawing.queue_draw()

    def quit_cb(self, widget):
        """
        Quit Gtk
        """
        Gtk.main_quit()


if __name__ == '__main__':
    gui = MyApp(parse_xrandr())
    Gtk.main()
