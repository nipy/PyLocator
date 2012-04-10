import gtk
import vtk
from events import EventHandler, UndoRegistry, Viewer

class MarkerListToolbar(gtk.Toolbar):
    """
    CLASS: ObserverToolbar
    DESCR:
    """

    def __init__(self, marker_list):
        gtk.Toolbar.__init__(self)

        self.marker_list = marker_list

        self.iconSize = gtk.ICON_SIZE_BUTTON
        
        self.set_border_width(0)
        self.set_style(gtk.TOOLBAR_ICONS)
        self.set_orientation(gtk.ORIENTATION_HORIZONTAL)

        self.buttons = {}

        self.__add_button(gtk.STOCK_ADD, 
                    'Add', 
                    'Add new marker by entering its coordinates',
                    self.marker_list.cb_add)
        self.__add_button(gtk.STOCK_REMOVE, 
                    'Remove', 
                    'Remove selected marker',
                    self.marker_list.cb_remove)
        self.__add_button(gtk.STOCK_GO_UP, 
                    'Move up', 
                    'Move selected marker up in list',
                    self.marker_list.cb_move_up)
        self.__add_button(gtk.STOCK_GO_DOWN, 
                    'Move down', 
                    'Move selected marker down in list',
                    self.marker_list.cb_move_down)
        self.__add_button(gtk.STOCK_EDIT, 
                    'Position', 
                    'Edit position of marker',
                    self.marker_list.cb_edit_position)
        self.__add_button(gtk.STOCK_SELECT_COLOR, 
                    'Color', 
                    'Select color for marker',
                    self.marker_list.cb_choose_color)

        for button in self.buttons.values():
            print button
            button.Sensitive=False

    def __add_button(self,stock, title, tooltip,callback):
        iconw = gtk.Image() # icon widget
        iconw.set_from_stock(stock, self.iconSize)
        button = self.append_item(title,tooltip,'Private',iconw,callback)
        self.buttons[title]=button
        return button
