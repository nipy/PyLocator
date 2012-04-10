from __future__ import division
import sys, os
import vtk

import gobject
import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu

colorSeq = (
    ( 'light skin' , (0.953, 0.875, 0.765)    ),
    ( 'dark skin'  , (0.624, 0.427, 0.169)    ),
    ( 'electrodes' , (0.482, 0.737, 0.820)    ),
    ( 'bone'       , (0.9804, 0.9216, 0.8431) ),
    )


colord = dict(colorSeq)

class ColorChooser(gtk.Frame):
    def __init__(self,color=None):
        gtk.Frame.__init__(self)
        self.da = gtk.DrawingArea()
        self.add(self.da)
        self.da.set_size_request(40,20)
        if color==None:
            color=gtk.gdk.Color(1.,1.,1.)
        self.set_color(color)
        self.set_border_width(20)
        self.set_property("shadow-type",gtk.SHADOW_ETCHED_IN)
        self.da.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.da.connect("button-press-event",self.choose_color)

    def set_color(self,color):
        for state in [gtk.STATE_NORMAL,
                      gtk.STATE_ACTIVE,
                      gtk.STATE_PRELIGHT,
                      gtk.STATE_SELECTED,
                      gtk.STATE_INSENSITIVE]:
            self.da.modify_bg(state,color)
        self._color=color
        self.emit("color_changed")

    def get_color(self):
        return self._color

    def choose_color(self, *args):
        new_color = choose_one_color(
                'Choose color for ROI',
                self._color
                )
        if new_color != self._color:
            self.set_color(new_color)
            
    color = property(get_color,set_color)

gobject.type_register(ColorChooser)
gobject.signal_new("color_changed", 
                   ColorChooser, 
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())

def choose_one_color(title, previous_color):
    dialog = gtk.ColorSelectionDialog(title)
        
    colorsel = dialog.colorsel

    
    colorsel.set_previous_color(previous_color)
    colorsel.set_current_color(previous_color)
    colorsel.set_has_palette(True)

    response = dialog.run()
    color = colorsel.get_current_color()
    dialog.destroy()
    
    if response == gtk.RESPONSE_OK:
        return color
    else:
        return previous_color
    
def tuple2gdkColor(colorTuple):
    return gtk.gdk.Color(
            65535.*colorTuple[0],
            65535.*colorTuple[1],
            65535.*colorTuple[2]
    )

def gdkColor2tuple(color):
    return [float(x)/65535. for x in (color.red,color.green,color.blue)]
