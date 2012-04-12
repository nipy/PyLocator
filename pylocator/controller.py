import os
import gtk
from shared import shared
from events import EventHandler
from vtkNifti import vtkNiftiImageReader

from gtkutils import simple_msg

import pylocator

class PyLocatorController(object):
    def __init__(self, window):
        self.window = window

    def load_markers(self, *args):
        dialog = gtk.FileSelection('Choose filename for marker info')
        dialog.set_filename(shared.get_last_dir())

        dialog.show()        
        response = dialog.run()
        
        if response==gtk.RESPONSE_OK:
            fname = dialog.get_filename()
            dialog.destroy()
            try: EventHandler().load_markers_from(fname)
            except IOError:
                error_msg(
                    'Could not load markers from %s' % fname, 
                    )
            
            else:
                shared.set_file_selection(fname)
                self.markersFileName = fname
        else: dialog.destroy()

    def save_markers(self, *args):
        try: self.markersFileName
        except AttributeError:
            self.save_as(*args)
        else: EventHandler().save_markers_as(self.markersFileName)

    def save_markers_as(self, *args):
        def ok_clicked(w):
            fname = dialog.get_filename()
            shared.set_file_selection(fname)
            try: EventHandler().save_markers_as(fname)
            except IOError:
                error_msg('Could not save data to %s' % fname,
                          )
            else:
                self.markersFileName = fname
                dialog.destroy()

        dialog = gtk.FileSelection('Choose filename for marker')
        dialog.set_filename(shared.get_last_dir())
        dialog.ok_button.connect("clicked", ok_clicked)
        dialog.cancel_button.connect("clicked", lambda w: dialog.destroy())
        dialog.show()
        pass

    def gtk_main_quit(self, *args):
        self.window.destroy()
        gtk.main_quit()

    def load_nifti(self, filename):
        if filename==None:
            dialog = gtk.FileSelection('Choose nifti file')
            #dialog = gtk.FileChooserDialog('Choose nifti file')
            #dialog.set_transient_for(widgets['dlgReader'])
            dialog.set_filename(shared.get_last_dir())
            response = dialog.run()
            filename = dialog.get_filename()
            dialog.destroy()
            if response == gtk.RESPONSE_OK:
                print "Loading:", filename
            else:
                return False

        shared.set_file_selection(filename)
        
        reader = vtkNiftiImageReader()
        reader.SetFileName(filename)
        reader.Update()

        if not reader:
            return False
        else:
            imageData = reader.GetOutput()
            EventHandler().notify('set image data', imageData)
            EventHandler().notify("set axes directions")
            EventHandler().setNifti(reader.GetQForm(),reader.nifti_voxdim,reader.shape)
            return True

    def set_mouse_interact_mode(self, menuItem, *args):
        """Sets the interaction mode of all marker window interactors
        Uses a mapping from menu item label to command.
        """
        commmands = {
                "_Mouse Interact" : "mouse1 interact",
                "_VTK Interact" : "vtk interact",
                "Set _Label" : "mouse1 label",
                "_Select Markers" : "mouse1 select",
                "Set _Color" : "mouse1 color",
                "_Move Markers" : "mouse1 move",
                "_Delete Markers" : "mouse1 delete"
        }

        if menuItem.get_active():
            menuItemLabel = menuItem.get_label()
            #print menuItemLabel, commmands[menuItemLabel]
            EventHandler().notify(commmands[menuItemLabel])

    def align_planes_to_surf_view(self, *args):
        fpu = self.window.surfRenWin.get_camera_fpu()
        self.window.pwxyz.set_camera(fpu)
        self.window.pwxyz.Render()

    def align_surf_to_planes_view(self, *args):
        fpu = self.window.pwxyz.get_camera_fpu()
        self.window.surfRenWin.set_camera(fpu)
        self.window.surfRenWin.Render()

    def show_about_dialog(self,item,*args):
        simple_msg("PyLocator Version %s" % pylocator.__version__)

    def open_help(self,item,*args):
        pass

    def __update_title_of_window(self, filename):
        pass

