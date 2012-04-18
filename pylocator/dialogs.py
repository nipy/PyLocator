import gtk
import re
from resources import edit_label_dialog, edit_coordinates_dialog, edit_settings_dialog, about_dialog
from gtkutils import str2num_or_err
from colors import gdkColor2tuple, tuple2gdkColor
from events import EventHandler
from shared import shared


def edit_label(oldLabel="", description=None):
    builder = gtk.Builder()
    builder.add_from_file(edit_label_dialog)
    dialog = builder.get_object("dialog")
    entry = builder.get_object("entry")
    entry.set_text(oldLabel)
    if description!=None:
        label1 = builder.get_object("label1")
        label1.set_text(description)

    response = dialog.run()

    if response==gtk.RESPONSE_OK:
        label = entry.get_text()
    else:
        label = None

    dialog.destroy()
    return label

def edit_label_of_marker(marker):
    label = marker.get_label()
    defaultLabel = label
    print defaultLabel, shared.lastLabel
    if defaultLabel=='' and shared.lastLabel is not None:
        m = re.match('(.+?)(\d+)', shared.lastLabel)
        if m:
            num = str(int(m.group(2))+1).zfill(len(m.group(2)))
            defaultLabel = m.group(1) + num
    print defaultLabel
        
    new_label = edit_label(defaultLabel)
    if shared.debug: print new_label, label

    if new_label==None or new_label==label: return
    EventHandler().notify('label marker', marker, new_label)
    shared.lastLabel = new_label

    
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

def about(version="0.xyz"):
    builder = gtk.Builder()
    builder.add_from_file(about_dialog)
    dialog = builder.get_object("dialog")
    label = builder.get_object("label2")

    label.set_text(label.get_text().replace("__version__",version))

    dialog.run()

    dialog.destroy()
    return label



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
        self.po.set_value(shared.planes_opacity)

        self.mo.set_value(shared.markers_opacity)
        self.ms.set_value(shared.marker_size)

        old_color = EventHandler().get_default_color()
        self.dc.set_color(tuple2gdkColor(old_color))

    def marker_opacity_changed(self, *args):
        val = self.mo.get_value()
        for marker in EventHandler().get_markers_as_seq():
            marker.GetProperty().SetOpacity(val)
        shared.marker_opacity = val
        EventHandler().notify("render now")

    def marker_size_changed(self, *args):
        val = self.ms.get_value()
        for marker in EventHandler().get_markers_as_seq():
            marker.set_size(val)
        shared.marker_size = val
        EventHandler().notify("render now")

    def planes_opacity_changed(self, *args):
        val = self.po.get_value()
        for pw in self.__get_plane_widgets():
            pw.GetTexturePlaneProperty().SetOpacity(val)
            pw.GetPlaneProperty().SetOpacity(val)
        shared.planes_opacity = val
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

