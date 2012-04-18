import os.path


#GTK Builder files
main_window = os.path.join(os.path.split(__file__)[0],"resources/mainWindow.glade")
edit_label_dialog = os.path.join(os.path.split(__file__)[0],"resources/editLabel.glade")
edit_coordinates_dialog = os.path.join(os.path.split(__file__)[0],"resources/editCoordinates.glade")
edit_settings_dialog = os.path.join(os.path.split(__file__)[0],"resources/editSettings.glade")
about_dialog = os.path.join(os.path.split(__file__)[0],"resources/about.glade")

#image files
camera_fn = os.path.join(os.path.split(__file__)[0],"resources/camera48.png")
camera_small_fn = os.path.join(os.path.split(__file__)[0],"resources/camera24.png")

if __name__=="__main__":
    import gtk
    builder = gtk.Builder()
    builder.add_from_file(main_window)
    win = builder.get_object("pylocatorMainWindow")
    win.show_all()
    gtk.main()
