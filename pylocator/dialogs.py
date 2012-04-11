import gtk
from pylocator_glade import edit_label_dialog, edit_coordinates_dialog
from gtkutils import str2num_or_err

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

if __name__=="__main__":
    gtk.idle_add(lambda: edit_label("test"))
    gtk.main_loop()
