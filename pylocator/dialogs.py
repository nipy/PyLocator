import gtk
from pylocator_glade import edit_label_dialog, edit_coordinates_dialog, edit_settings_dialog
from gtkutils import str2num_or_err
from colors import gdkColor2tuple, tuple2gdkColor
from events import EventHandler

def edit_label(oldLabel=""):
    builder = gtk.Builder()
    builder.add_from_file(edit_label_dialog)
    dialog = builder.get_object("dialog")
    entry = builder.get_object("entry")

    entry.set_text(oldLabel)

    response = dialog.run()

    if response==gtk.RESPONSE_OK:
        label = entry.get_text()
    else:
        label = None

    dialog.destroy()
    return label
    
def edit_coordinates(X=0,Y=0,Z=0, description=None):
    builder = gtk.Builder()
    builder.add_from_file(edit_coordinates_dialog)
    dialog = builder.get_object("dialog")
    labelDescription = builder.get_object("labelDescription")
    entryX = builder.get_object("entry1")
    entryY = builder.get_object("entry2")
    entryZ = builder.get_object("entry3")

    if description!=None:
        labelDescription.set_text(description)

    for ax, entry in zip((X,Y,Z),(entryX,entryY,entryZ)):
        entry.set_text("%.3f"%ax)

    while 1:
        response = dialog.run()

        if response==gtk.RESPONSE_OK:
            val1 = str2num_or_err(entryX.get_text(), "X", None)
            if val1 is None: continue
            val2 = str2num_or_err(entryY.get_text(), "Y", None)
            if val2 is None: continue
            val3 = str2num_or_err(entryZ.get_text(), "Z", None)
            if val3 is None: continue

            rv= val1, val2, val3
        else: rv = None
        break

    dialog.destroy()
    return rv

class SettingsController(object):
    def __init__(self, pwxyz):
        self.pwxyz = pwxyz

        builder = gtk.Builder()
        builder.add_from_file(edit_settings_dialog)

        self.dialog = builder.get_object("dialog")
        self.mo = builder.get_object("marker_opacity")
        self.ms = builder.get_object("marker_size")
        self.po = builder.get_object("planes_opacity")
        self.dc = builder.get_object("colorbutton")

        self.__get_current_values()

        builder.connect_signals(self)

    def __get_current_values(self):
        self.po.set_value(self.pwxyz.pwX.GetTexturePlaneProperty().GetOpacity())

        markers = EventHandler().get_markers_as_seq()
        if len(markers)>0:
            old_mo = markers[0].GetProperty().GetOpacity()
            self.mo.set_value(old_mo)
            old_ms = markers[0].get_size()
            self.ms.set_value(old_ms)

        old_color = EventHandler().get_default_color()
        self.dc.set_color(tuple2gdkColor(old_color))

    def marker_opacity_changed(self, *args):
        val = self.mo.get_value()
        for marker in EventHandler().get_markers_as_seq():
            marker.GetProperty().SetOpacity(val)
        EventHandler().notify("render now")

    def marker_size_changed(self, *args):
        val = self.ms.get_value()
        for marker in EventHandler().get_markers_as_seq():
            marker.set_size(val)
        EventHandler().notify("render now")

    def planes_opacity_changed(self, *args):
        val = self.po.get_value()
        for pw in self.__get_plane_widgets():
            pw.GetTexturePlaneProperty().SetOpacity(val)
            pw.GetPlaneProperty().SetOpacity(val)
        self.pwxyz.Render()

    def set_default_color(self, *args):
        color = self.dc.get_color()
        EventHandler().set_default_color(gdkColor2tuple(color))

    def close_dialog(self, *args):
        print "close dialog"
        self.dialog.hide()
        self.dialog.destroy()

    def __get_plane_widgets(self):
        pwx = self.pwxyz.pwX
        pwy = self.pwxyz.pwY
        pwz = self.pwxyz.pwZ
        return pwx, pwy, pwz

