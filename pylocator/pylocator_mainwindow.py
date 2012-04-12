#! /usr/bin/python

import gobject, gtk
import os.path

from surf_renderer import SurfRenderWindow
from plane_widgets_xyz import PlaneWidgetsXYZ, move_pw_to_point
from plane_widgets_observer import PlaneWidgetObserver
from plane_widgets_observer_toolbar import ObserverToolbar

from surf_renderer_props import SurfRendererProps
from roi_renderer_props import RoiRendererProps
from screenshot_props import ScreenshotProps

from marker_list import MarkerList

from controller import PyLocatorController

from shared import shared

from gtkutils import error_msg

from pylocator_glade import main_window

def run_pylocator(filename=None, surface=None):
    """main method to run when PyLocator is started"""
    __global_preparations()
    window = create_mainwindow()
    loadingSuccessful = window.controller.load_nifti(filename)
    window.controller.align_surf_to_planes_view()
    if loadingSuccessful:
        window.show()
        gtk.main()

def __global_preparations():
    user_dir = __find_userdir()
    shared.set_file_selection(user_dir)

def create_mainwindow():
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

    __fill_notebook_pages(window, vboxes)
    __add_observer_widgets_to_window(window,hboxSlices)
    __set_screenshot_properties(window)
    
    window.screenshot_props.create_buttons()

    controller = PyLocatorController(window)
    builder.connect_signals(controller)
    window.controller = controller
    return window

def __fill_notebook_pages(window, vboxes):
    window.marker_list = MarkerList()
    #window.marker_list._treev_sel.connect("changed",self.on_marker_selection_changed)
    vboxes["Markers"].pack_start(window.marker_list,True,True)

    window.surf_ren_props = SurfRendererProps(window.surfRenWin, window.pwxyz)
    vboxes["Surfaces"].pack_start(window.surf_ren_props)

    window.roi_props = RoiRendererProps(window.surfRenWin, window.pwxyz)
    vboxes["ROI"].pack_start(window.roi_props)

    window.screenshot_props = ScreenshotProps()
    vboxes["Screenshots"].pack_start(window.screenshot_props)

def __add_observer_widgets_to_window(win,hbox):
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

def __set_screenshot_properties(window):
    # set screenshot properties for all render windows
    screenshot_properties = [
        (window.pwxyz,          "Three planes"),
        (window.surfRenWin,     "Surface"),
        (window.observers[0],   "Slice 1"),
        (window.observers[1],   "Slice 2"),
        (window.observers[2],   "Slice 3"),
    ]
    for widget, name in screenshot_properties:
        widget.set_screenshot_props(window.screenshot_props,name)

def __find_userdir():
    userdir = os.path.expanduser("~")
    try:
        from win32com.shell import shellcon, shell
        userdir = shell.SHGetFolderPath(0,shellcon.CSIDL_PERSONAL,0,0)
    except ImportError,ie:
        userdir = os.path.expanduser("~")
    return userdir

if __name__=="__main__":
    win = create_new_mainwindow_using_glade()
    win.show_all()
    gtk.main()
