# shape.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo
import math

from .tools import ToolTemplate

class ToolShape(ToolTemplate):
	__gtype_name__ = 'ToolShape'

	use_size = True
	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Basic shape"), 'radio-symbolic', window)

		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.selected_style_label = _("Filled (secondary color)")
		self.selected_shape_label = _("Rectangle")
		self.selected_style_id = 'secondary'
		self.selected_shape_id = 'rectangle'

		self.add_tool_action_enum('shape_shape', 'rectangle', self.on_change_active_shape)
		self.add_tool_action_enum('shape_style', 'secondary', self.on_change_active_style)

	def on_change_active_style(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")
		self.window.set_picture_title()

	def on_change_active_shape(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		self.selected_shape_id = state_as_string
		if state_as_string == 'rectangle':
			self.selected_shape_label = _("Rectangle")
		elif state_as_string == 'oval':
			self.selected_shape_label = _("Oval")
		else:
			self.selected_shape_label = _("Circle")
		self.window.set_picture_title()

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/tools/ui/tool_shape.ui')
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_shape_label

	def get_edition_status(self):
		label = self.label + ' -' + self.selected_shape_label + ' - ' + \
			self.selected_style_label
		return label

	def give_back_control(self):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.restore_pixbuf()
		return False

	def draw_rectangle(self, event_x, event_y):
		w_context = cairo.Context(self.get_surface())
		w_context.move_to(self.x_press, self.y_press)
		w_context.line_to(self.x_press, event_y)
		w_context.line_to(event_x, event_y)
		w_context.line_to(event_x, self.y_press)
		w_context.close_path()
		self._path = w_context.copy_path()

	def draw_oval(self, event_x, event_y):
		w_context = cairo.Context(self.get_surface())
		w_context.curve_to(self.x_press, (self.y_press+event_y)/2, \
			self.x_press, event_y, \
			(self.x_press+event_x)/2, event_y)
		w_context.curve_to((self.x_press+event_x)/2, event_y, \
			event_x, event_y, \
			event_x, (self.y_press+event_y)/2)
		w_context.curve_to(event_x, (self.y_press+event_y)/2, \
			event_x, self.y_press, \
			(self.x_press+event_x)/2, self.y_press)
		w_context.curve_to((self.x_press+event_x)/2, self.y_press, \
			self.x_press, self.y_press, \
			self.x_press, (self.y_press+event_y)/2)
		w_context.close_path()
		self._path = w_context.copy_path()

	def draw_circle(self, event_x, event_y):
		w_context = cairo.Context(self.get_surface())
		rayon = math.sqrt((self.x_press - event_x)*(self.x_press - event_x) \
			+ (self.y_press - event_y)*(self.y_press - event_y))
		w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
		self._path = w_context.copy_path()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		if self.selected_shape_id == 'rectangle':
			self.draw_rectangle(event_x, event_y)
		elif self.selected_shape_id == 'oval':
			self.draw_oval(event_x, event_y)
		elif self.selected_shape_id == 'circle':
			self.draw_circle(event_x, event_y)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color
		else:
			self.main_color = left_color
			self.secondary_color = right_color

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if self.selected_shape_id == 'rectangle':
			self.draw_rectangle(event_x, event_y)
		elif self.selected_shape_id == 'oval':
			self.draw_oval(event_x, event_y)
		elif self.selected_shape_id == 'circle':
			self.draw_circle(event_x, event_y)
		self.x_press = 0.0
		self.y_press = 0.0
		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'operator': cairo.Operator.OVER,
			'line_width': self.tool_width,
			'filling': self.selected_style_id,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		w_context.set_operator(operation['operator'])
		w_context.set_line_width(operation['line_width'])
		rgba_main = operation['rgba_main']
		rgba_secd = operation['rgba_secd']
		w_context.append_path(operation['path'])
		filling = operation['filling']
		if filling == 'secondary':
			w_context.set_source_rgba(rgba_secd.red, rgba_secd.green, rgba_secd.blue, rgba_secd.alpha)
			w_context.fill_preserve()
			w_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
			w_context.stroke()
		elif filling == 'filled':
			w_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
			w_context.fill()
		else:
			w_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
			w_context.stroke()
