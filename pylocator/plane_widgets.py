# http://www.vtk.org/doc/nightly/html/classvtkInteractorStyle.html defines the key events
from __future__ import division

import vtk

import gtk

import re, time
from gtk import gdk
from scipy import array
from scipy import mean
#from image_reader import widgets, GladeHandlers
from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posnum_or_err, ProgressBarDialog, make_option_menu, MyToolbar

from markers import Marker, RingActor
from events import EventHandler, UndoRegistry, Viewer
from shared import shared
from surf_renderer import SurfRenderWindow
from surf_renderer_props import SurfRendererProps
from roi_renderer_props import RoiRendererProps
from marker_list import MarkerList
from screenshot_taker import ScreenshotProps #ScreenshotTaker

import scipy

INTERACT_CURSOR, MOVE_CURSOR, COLOR_CURSOR, SELECT_CURSOR, DELETE_CURSOR, LABEL_CURSOR, SCREENSHOT_CURSOR = gtk.gdk.ARROW, gtk.gdk.HAND2, gtk.gdk.SPRAYCAN, gtk.gdk.TCROSS, gtk.gdk.X_CURSOR, gtk.gdk.PENCIL, gtk.gdk.ICON
        

from plane_widgets_xyz import PlaneWidgetsXYZ, move_pw_to_point
from plane_widgets_observer import PlaneWidgetObserver
#from plane_widgets_observer_mri import PlaneWidgetObserverMRI
from plane_widgets_observer_toolbar import ObserverToolbar
from pylocator_maintoolbar import MainToolbar
from pylocator_interactortoolbar import InteractorToolbar

        
class PlaneWidgetsWithObservers(gtk.VBox):

    """
    def translation_changed(self, entry, data):
        if shared.debug: print 'entry=',entry, 'data=', data, 'val=', entry.get_text()
        self.pwxyz.translate_vtk(data, float(entry.get_text()))

    def rotation_changed(self, entry, data):
        if shared.debug: print 'entry=',entry, 'data=', data, 'val=', entry.get_text()
        self.pwxyz.rotate_vtk(data, float(entry.get_text()))
    """

    """
    CLASS: PlaneWidgetsWithObservers
    DESC: controls:
        - PlaneWidgetsXYZ
        - SurfRenderWindow
        - MainToolbar
        - InteractorToolbar
        - SurfRendererProps
    """
    def __init__(self, mainWindow, imageData=None):
        gtk.VBox.__init__(self, spacing=3)
        self.mainWindow = mainWindow
        border = 5
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetsXYZ()"
        self.pwxyz = PlaneWidgetsXYZ()
        self.pwxyz.show()


        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): SurfRenderWindow()"
        self.surfRenWin = SurfRenderWindow()
        self.surfRenWin.show()
        
        toolbar = MainToolbar(owner=self)
        toolbar.show()
        toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)

        # add MainToolbar to window
        self.pack_start(toolbar, False, False)
        self.mainToolbar = toolbar
        
        toolbarInteractor = InteractorToolbar()
        toolbarInteractor.show()
        toolbarInteractor.set_orientation(gtk.ORIENTATION_VERTICAL)        

        self.dlgSurf = SurfRendererProps(self.surfRenWin, self.pwxyz)
        self.dlgRoi = RoiRendererProps(self.surfRenWin, self.pwxyz)

        self.dlgScreenshots = ScreenshotProps()

        vboxTools = gtk.VBox()
        vboxTools.show()
        
        hbox = gtk.HBox(spacing=border)
        #hbox.set_border_width(border)
        hbox.show()

        # add InteractorToolbar to vboxTools
        vboxTools.pack_start(toolbarInteractor, True, True)
        # add vboxTools to hbox
        # xxx: mcc
        #self.pack_start(vboxTools, False, False)
        hbox.pack_start(vboxTools, False, True)
        # add hbox to window
        self.pack_start(hbox, True, True)


        # also add a table of x y z translation and dx dy dz rotation values
        """
        hack_table = gtk.VBox()
        
        entry_x = gtk.Entry()
        entry_x.connect("activate", self.translation_changed, 'x')
        entry_x.set_text('0')
        entry_x.set_width_chars(6)
        hack_table.pack_start(entry_x, False, False)

        entry_x = gtk.Entry()
        entry_x.connect("activate", self.translation_changed, 'y')
        entry_x.set_text('0')
        entry_x.set_width_chars(6)
        hack_table.pack_start(entry_x, False, False)

        entry_x = gtk.Entry()
        entry_x.connect("activate", self.translation_changed, 'z')
        entry_x.set_text('0')
        entry_x.set_width_chars(6)
        hack_table.pack_start(entry_x, False, False)

        entry_x = gtk.Entry()
        entry_x.connect("activate", self.rotation_changed, 'x')
        entry_x.set_text('0')
        entry_x.set_width_chars(6)
        hack_table.pack_start(entry_x, False, False)

        entry_x = gtk.Entry()
        entry_x.connect("activate", self.rotation_changed, 'y')
        entry_x.set_text('0')
        entry_x.set_width_chars(6)
        hack_table.pack_start(entry_x, False, False)

        entry_x = gtk.Entry()
        entry_x.connect("activate", self.rotation_changed, 'z')
        entry_x.set_text('0')
        entry_x.set_width_chars(6)
        hack_table.pack_start(entry_x, False, False)

        hack_table.show_all()

        hbox.pack_start(hack_table, False, False)
        """

        vpaned = gtk.VPaned()
        #vbox.set_border_width(border)
        # add vbox to hbox
        hbox.pack_start(vpaned, True, True)


        #Upper line of widgets consists of two packed HPaned
        upperPaned1 = gtk.HPaned()
        upperPaned2 = gtk.HPaned()
        upperPaned1.pack2(upperPaned2,True,True)
        # add PlaneWidgetsXYZ to upperPaned1
        upperPaned1.pack1(self.pwxyz, True, True)
        # add surfRenderWindow to upperPaned2
        upperPaned2.pack1(self.surfRenWin, True, True)
        # Create marker list
        self.marker_list = MarkerList()
        self.marker_list.show_all()
        self.marker_list._treev_sel.connect("changed",self.on_marker_selection_changed)
        upperPaned2.pack2(self.marker_list, True, True)
        # add hboxUpper to vbox
        vpaned.pack1(upperPaned1, True, True)

        #Share space for the HPaned-instances
        #width = upperPaned1.get_property("max-position")
        #print "width", width
        upperPaned1.set_position(300)
        upperPaned2.set_position(300)

        pwx, pwy, pwz = self.pwxyz.get_plane_widgets_xyz()


        hbox = gtk.HBox(spacing=border)
        #hbox.set_border_width(border)
        hbox.show()
        # add hbox to vbox

        vpaned.pack2(hbox, True, True)

        vboxObs = gtk.VBox()
        vboxObs.show()
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetObserver(pwx)"
        self.observerX = PlaneWidgetObserver(pwx, owner=self, orientation=0)
        self.observerX.show()

        # add observerX to vboxObs
        vboxObs.pack_start(self.observerX, True, True)
        toolbarX = ObserverToolbar(self.observerX)
        toolbarX.show()
        # add vboxObs to hbox
        vboxObs.pack_start(toolbarX, False, False)
        hbox.pack_start(vboxObs, True, True)

        vboxObs = gtk.VBox()
        vboxObs.show()
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetObserver(pwy)"
        self.observerY = PlaneWidgetObserver(pwy, owner=self, orientation=1)
        self.observerY.show()
        vboxObs.pack_start(self.observerY, True, True)
        toolbarY = ObserverToolbar(self.observerY)
        toolbarY.show()
        vboxObs.pack_start(toolbarY, False, False)
        # add vboxObs to hbox
        hbox.pack_start(vboxObs, True, True)

        vboxObs = gtk.VBox()
        vboxObs.show()
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetObserver(pwz)"
        self.observerZ = PlaneWidgetObserver(pwz, owner=self, orientation=2)
        self.observerZ.show()
        vboxObs.pack_start(self.observerZ, True, True)
        toolbarZ = ObserverToolbar(self.observerZ)
        toolbarZ.show()
        vboxObs.pack_start(toolbarZ, False, False)
        hbox.pack_start(vboxObs, True, True)

        #Register ScreenshotProps for all widgets
        #for st in [self.surfRenWin,self.pwxyz,self.observerX,self.observerY,self.observerZ]:
        #for st in [self.pwxyz,self.observerX,self.observerY,self.observerZ]:
        self.pwxyz.set_screenshot_props(self.dlgScreenshots,"Three planes")
        self.surfRenWin.set_screenshot_props(self.dlgScreenshots,"Surface")
        self.observerX.set_screenshot_props(self.dlgScreenshots,"Slice 1")
        self.observerY.set_screenshot_props(self.dlgScreenshots,"Slice 2")
        self.observerZ.set_screenshot_props(self.dlgScreenshots,"Slice 3")

        vpaned.show_all()
        #Share space for the HPaned-instances
        #height = vpaned.get_property("max-position")
        #print "height", height
        vpaned.set_position(250)

        #for pw in self.pwxyz.get_plane_widgets_xyz():
        #    move_pw_to_point(pw,self.pwxyz.imageData.GetCenter())

        ### XXX mcc
        """        
        hbox = gtk.HBox(spacing=border)
        hbox.show()
        vbox.pack_start(hbox, True, True)
        vboxObsMRI = gtk.VBox()
        vboxObsMRI.show()
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetObserver(pwx)"
        self.observerX = PlaneWidgetObserverMRI(pwx, owner=self, orientation=0)
        self.observerX.show()
        vboxObsMRI.pack_start(self.observerX, True, True)
        toolbarX = ObserverToolbar(self.observerX)
        toolbarX.show()
        vboxObsMRI.pack_start(toolbarX, False, False)
        hbox.pack_start(vboxObsMRI, True, True)

        vboxObsMRI = gtk.VBox()
        vboxObsMRI.show()
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetObserver(pwy)"
        self.observerY = PlaneWidgetObserverMRI(pwy, owner=self, orientation=1)
        self.observerY.show()
        vboxObsMRI.pack_start(self.observerY, True, True)
        toolbarY = ObserverToolbar(self.observerY)
        toolbarY.show()
        vboxObsMRI.pack_start(toolbarY, False, False)
        hbox.pack_start(vboxObsMRI, True, True)

        vboxObsMRI = gtk.VBox()
        vboxObsMRI.show()
        if shared.debug: print "PlaneWidgetsWithObservers.__init__(): PlaneWidgetObserver(pwz)"
        self.observerZ = PlaneWidgetObserverMRI(pwz, owner=self, orientation=2)
        self.observerZ.show()
        vboxObsMRI.pack_start(self.observerZ, True, True)
        toolbarZ = ObserverToolbar(self.observerZ)
        toolbarZ.show()
        vboxObsMRI.pack_start(toolbarZ, False, False)
        hbox.pack_start(vboxObsMRI, True, True)

        ### XXX mcc

        #self.pwxyz.set_size_request(450, 150)
        #self.observerX.set_size_request(150, 150)
        #self.observerY.set_size_request(150, 150)
        #self.observerZ.set_size_request(150, 150)

        # render all observers on interaction events with plane
        # widgets to allow common window level settings
        pwx.AddObserver('InteractionEvent', self.render_observers)
        pwy.AddObserver('InteractionEvent', self.render_observers)
        pwz.AddObserver('InteractionEvent', self.render_observers)
        #self.set_image_data(imageData)
        """
        
        self.observerX.observer.AddObserver('InteractionEvent', self.dlgSurf.interaction_event)
        self.observerY.observer.AddObserver('InteractionEvent', self.dlgSurf.interaction_event)
        self.observerZ.observer.AddObserver('InteractionEvent', self.dlgSurf.interaction_event)

    def set_image_data(self, imageData):
        if imageData is None: return 
        self.pwxyz.set_image_data(imageData)
        self.surfRenWin.set_image_data(imageData)
        self.observerX.set_image_data(imageData)
        self.observerY.set_image_data(imageData)
        self.observerZ.set_image_data(imageData)
        
        
    def get_observer_x(self):
        return self.observerX

    def get_observer_y(self):
        return self.observerY

    def get_observer_z(self):
        return self.observerZ

    def get_plane_widget_x(self):
        return self.pwxyz.get_plane_widget_x()

    def get_plane_widget_y(self):
        return self.pwxyz.get_plane_widget_y()

    def get_plane_widget_z(self):
        return self.pwxyz.get_plane_widget_z()

    def get_plane_widget_xyz(self):
        return self.pwxyz


    def render_observers(self, *args):
        #if shared.debug: print 'rendering all'
        self.surfRenWin.Render()        
        self.observerX.Render()
        self.observerY.Render()
        self.observerZ.Render()
    
    def on_marker_selection_changed(self,*args):
        pass

    def destroy(self):
        for widg in [self.observerX,self.observerY,self.observerZ,self.pwxyz,self.surfRenWin]:
            widg.hide()
            widg.destroy()

