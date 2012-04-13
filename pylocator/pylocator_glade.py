import os.path


#GTK Builder files
main_window = os.path.join(os.path.split(__file__)[0],"gladefiles/mainWindow.glade")
edit_label_dialog = os.path.join(os.path.split(__file__)[0],"gladefiles/editLabel.glade")
edit_coordinates_dialog = os.path.join(os.path.split(__file__)[0],"gladefiles/editCoordinates.glade")
edit_settings_dialog = os.path.join(os.path.split(__file__)[0],"gladefiles/editSettings.glade")
about_dialog = os.path.join(os.path.split(__file__)[0],"gladefiles/about.glade")

#image files
camera_fn = os.path.join(os.path.split(__file__)[0],"gladefiles/camera48.png")
camera_small_fn = os.path.join(os.path.split(__file__)[0],"gladefiles/camera24.png")


#from pylocator_glade import glade_test
#print glade_test
#builder = gtk.Builder()
#builder.add_from_file(glade_test)
#win = builder.get_object("window1")
#win.show()

if __name__=="__main__":
    import gtk
    builder = gtk.Builder()
    builder.add_from_file(main_window)
    win = builder.get_object("pylocatorMainWindow")
    win.show_all()
    gtk.main()
