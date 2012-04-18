from __future__ import division

import gobject
import gtk

from gtkutils import make_option_menu

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
        self._ignore_updates = False
        self.da = gtk.DrawingArea()
        self.da.show()
        self.add(self.da)
        self.da.set_size_request(40,20)
        if color==None:
            color=gtk.gdk.Color(1.,1.,1.)
        self.set_color(color)
        self.set_border_width(5)
        self.set_property("shadow-type",gtk.SHADOW_ETCHED_IN)
        self.da.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.da.connect("button-press-event",self.choose_color)

    def _set_color(self,color,ignore_updates=True):
        try:
            self._ignore_updates = ignore_updates
            if not type(color) == gtk.gdk.Color:
                color = tuple2gdkColor(color)
            for state in [gtk.STATE_NORMAL,
                        gtk.STATE_ACTIVE,
                        gtk.STATE_PRELIGHT,
                        gtk.STATE_SELECTED,
                        gtk.STATE_INSENSITIVE]:
                self.da.modify_bg(state,color)
            self._color=color
            if not self._ignore_updates:
                self.emit("color_changed")
        finally:
            self._ignore_updates = False


    def set_color(self, color):
        self._set_color(color, False)

    def get_color(self):
        return self._color

    def choose_color(self, *args):
        new_color = choose_one_color(
                'Choose color...',
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

class ColorChooserWithPredefinedColors(gtk.HBox):
    custom_str = "custom..."
    def __init__(self, colorSeq=colorSeq):
        names, self.colors= zip(*colorSeq)
        self.colorDict = dict(colorSeq)

        self.colorNames = list(names)

        gtk.HBox.__init__(self)
        self._ignore_updates = False

        vb1 = gtk.VBox()
        vb2 = gtk.VBox()
        vb1.show()
        vb2.show()
        self.pack_start(vb1, False)
        self.pack_start(vb2, False)

        self.colorNames.append(self.custom_str)
        self.optmenu = make_option_menu(
           self.colorNames, self._ddlist_changed)
        self.optmenu.show()
        vb1.pack_start(self.optmenu, True, False)

        initial_color = self.colorDict[self.optmenu.get_active_text()]
        self.color_chooser = ColorChooser(initial_color)
        vb2.pack_start(self.color_chooser, True, False)
        self.color_chooser.connect("color_changed", self.color_changed)

        self.show()
    
    def _ddlist_changed(self, item, *args):
        s = item.get_active_text()
        if s==self.custom_str:
            self.color_chooser.show()
            if not self._ignore_updates:
                self.color_chooser.choose_color()
        else:
            self.color_chooser.hide()
            if not self._ignore_updates:
                self.color_chooser.set_color(tuple2gdkColor(self.colorDict[s]))

    def color_changed(self, *args):
        self.emit("color_changed")

    def get_color(self):
        return self.color_chooser.get_color()

    def _set_color(self,color,ignore_updates=True):
        try:
            self._ignore_updates=ignore_updates
            if type(color)==str:
                idx = self.colorNames.index(color)
                if not (idx>-1 and idx<len(self.colorNames)):
                    raise ValueError("Unknown color")
                self.optmenu.set_active(idx)
            else:
                self.optmenu.set_active(self.colorNames.index(self.custom_str))
                self.color_chooser._set_color(color, ignore_updates)
        finally:
            self._ignore_updates = False

    def set_color(self,color):
        self._set_color(color, False)

    def get_color_name(self):
        return self.optmenu.get_active_text()

    color = property(get_color,set_color)
    colorName = property(get_color_name)

gobject.type_register(ColorChooserWithPredefinedColors)
gobject.signal_new("color_changed", 
                   ColorChooserWithPredefinedColors, 
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
            int(65535.*colorTuple[0]),
            int(65535.*colorTuple[1]),
            int(65535.*colorTuple[2])
    )

def gdkColor2tuple(color):
    return [float(x)/65535. for x in (color.red,color.green,color.blue)]


if __name__=="__main__":
    def func(cc):
        print "Color changed", cc.get_color()

    win = gtk.Window()
    box = gtk.VBox()
    win.add(box)

    cc = ColorChooserWithPredefinedColors()
    box.pack_start(cc, False)

    cc.connect("color_changed",func)

    win.show_all()
    gtk.main()
    
