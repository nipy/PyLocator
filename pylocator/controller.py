import os
import gtk
from shared import shared
from events import EventHandler
from vtkNifti import vtkNiftiImageReader

from surf_renderer import SurfRenderWindow
from plane_widgets_xyz import PlaneWidgetsXYZ, move_pw_to_point
from plane_widgets_observer import PlaneWidgetObserver
from plane_widgets_observer_toolbar import ObserverToolbar

from surf_renderer_props import SurfRendererProps
from roi_renderer_props import RoiRendererProps
from screenshot_props import ScreenshotProps

from marker_list import MarkerList
from gtkutils import simple_msg

import pylocator
from resources import main_window
from dialogs import SettingsController, about

from colors import gdkColor2tuple

class PyLocatorController(object):
    def __init__(self):
        self.window = self.__create_mainwindow()
        self.__set_default_color()

    def __set_default_color(self):
        da = gtk.DrawingArea()
        cmap = da.get_colormap()
        self.lastColor = cmap.alloc_color(0, 0, 65535)

    def __create_mainwindow(self):
        """Read builder-XML file and create window.
        Inserts custom widgets at the desired positions
        """
        builder = gtk.Builder()
        builder.add_from_file(main_window)
        window = builder.get_object("pylocatorMainWindow")
        hpaned = {}
        for key in ["Main","Top"]:
            hpaned[key] = builder.get_object("hpaned%s"%key)
        hboxSlices = builder.get_object("hboxSlices")
        vboxes = {}
        for key in ["Markers","Surfaces","ROI","Screenshots"]:
            vboxes[key] = builder.get_object("vbox%s"%key)

        window.pwxyz = PlaneWidgetsXYZ()
        window.pwxyz.show()
        hpaned["Top"].pack1(window.pwxyz,True,True)

        window.surfRenWin = SurfRenderWindow()
        window.surfRenWin.show()
        hpaned["Top"].pack2(window.surfRenWin,True,True)

        self.__fill_notebook_pages(window, vboxes)
        self.__add_observer_widgets_to_window(window,hboxSlices)
        self.__set_screenshot_properties(window)
        
        window.screenshot_props.create_buttons()

        builder.connect_signals(self)
        
        return window

    def __fill_notebook_pages(self, window, vboxes):
        window.marker_list = MarkerList()
        #window.marker_list._treev_sel.connect("changed",self.on_marker_selection_changed)
        vboxes["Markers"].pack_start(window.marker_list,True,True)

        window.surf_ren_props = SurfRendererProps()
        vboxes["Surfaces"].pack_start(window.surf_ren_props)

        window.roi_props = RoiRendererProps()
        vboxes["ROI"].pack_start(window.roi_props)

        window.screenshot_props = ScreenshotProps()
        vboxes["Screenshots"].pack_start(window.screenshot_props)

    def __add_observer_widgets_to_window(self,win,hbox):
        win.observers = []
        for orientation, pw in zip(range(3),win.pwxyz.get_plane_widgets_xyz()):
            vboxObs = gtk.VBox()
            vboxObs.show()
            observer = PlaneWidgetObserver(pw, owner=win, orientation=orientation)
            observer.show()
            win.observers.append(observer)
            vboxObs.pack_start(observer, True, True)
            toolbar = ObserverToolbar(observer)
            toolbar.show()
            vboxObs.pack_start(toolbar, False, False)
            hbox.pack_start(vboxObs, True, True)
            observer.observer.AddObserver('InteractionEvent', win.surf_ren_props.interaction_event)

    def __set_screenshot_properties(self, window):
        # set screenshot properties for all render windows
        screenshot_properties = [
            (window.pwxyz,          "Three planes"),
            (window.surfRenWin,     "Surface"),
            (window.observers[0],   "Slice 1"),
            (window.observers[1],   "Slice 2"),
            (window.observers[2],   "Slice 3"),
        ]
        for widget, name in screenshot_properties:
            widget.set_screenshot_props(name)
            window.screenshot_props.append_screenshot_taker(widget)

    def get_render_windows(self):
        if self.window!=None:
            yield self.window.pwxyz
            yield self.window.surfRenWin
            for o in self.window.observers:
                yield o

    # Event handler stuff from here #########################

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
            EventHandler().set_nifti(reader)
            self.store_current_camera_fpus()
            EventHandler().notify("render now")
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

    def store_current_camera_fpus(self):
        for rw in self.get_render_windows():
            rw.store_camera_default()

    def reset_cameras(self, *args):
        for rw in self.get_render_windows():
            rw.reset_camera_to_default()

    def show_settings_dialog(self,*args):
        settings = SettingsController(self.window.pwxyz)
        settings.dialog.run()

    def choose_color(self, *args):
        dialog = gtk.ColorSelectionDialog('Choose default marker color')
        colorsel = dialog.colorsel
        colorsel.set_previous_color(self.lastColor)
        colorsel.set_current_color(self.lastColor)
        colorsel.set_has_palette(True)
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            color = colorsel.get_current_color()
            self.lastColor = color
            EventHandler().set_default_color(gdkColor2tuple(color))
            
        dialog.destroy()


    def show_about_dialog(self,item,*args):
        about(pylocator.__version__)

    def open_help(self,item,*args):
        pass

    def __update_title_of_window(self, filename):
        pass

