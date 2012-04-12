from gtk import gdk
import gtk
import vtk
from GtkGLExtVTKRenderWindowInteractor import GtkGLExtVTKRenderWindowInteractor
from events import EventHandler, UndoRegistry, Viewer
from gtkutils import error_msg
import re

from pylocator_glade import camera_small_fn

from shared import shared


INTERACT_CURSOR, MOVE_CURSOR, COLOR_CURSOR, SELECT_CURSOR, DELETE_CURSOR, LABEL_CURSOR, SCREENSHOT_CURSOR = gtk.gdk.ARROW, gtk.gdk.HAND2, gtk.gdk.SPRAYCAN, gtk.gdk.TCROSS, gtk.gdk.X_CURSOR, gtk.gdk.PENCIL, gtk.gdk.ICON

class PyLocatorRenderWindow(GtkGLExtVTKRenderWindowInteractor):
    def __init__(self,*args):
        GtkGLExtVTKRenderWindowInteractor.__init__(self,*args)
        self.screenshot_button_label = "_render window_"

        EventHandler().attach(self)
        self.interactButtons = (1,2,3)
        self.renderOn = 1
        self.Initialize()
        self.Start()

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0,0,0)
        self.renWin = self.GetRenderWindow()
        self.renWin.AddRenderer(self.renderer)
        self.interactor = self.renWin.GetInteractor()

        self.camera_default_fpu = None

    def Render(self):
        if self.renderOn:
            GtkGLExtVTKRenderWindowInteractor.Render(self)

    def get_camera_fpu(self):
        camera = self.renderer.GetActiveCamera()
        return (camera.GetFocalPoint(),
                camera.GetPosition(),
                camera.GetViewUp())

    def set_camera(self, fpu):
        camera = self.renderer.GetActiveCamera()
        focal, position, up = fpu
        camera.SetFocalPoint(focal)
        camera.SetPosition(position)
        camera.SetViewUp(up)
        self.renderer.ResetCameraClippingRange()
        self.Render()

    def store_camera_default(self):
        self.camera_default_fpu = self.get_camera_fpu()

    def reset_camera_to_default(self):
        fpu = self.camera_default_fpu
        if fpu != None:
            self.set_camera(fpu)

    def take_screenshot(self, fn_pattern, magnification=1):
        #print "Start Screenshot"
        if not fn_pattern:
            error_msg("Cannot take screenshot: No filename pattern given.")
            return False

        fn = fn_pattern%shared.screenshot_cnt
        mag = int(round(magnification))

        shared.screenshot_cnt+=1

        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(self.renWin)
        w2if.SetMagnification(mag) #shared.screenshot_magnification)
        w2if.Update()
         
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(fn)
        writer.SetInput(w2if.GetOutput())
        writer.Write()
        #print "Ende Screenshot"
        self.Render()
        return

    def set_screenshot_props(self, label):
        self.screenshot_button_label = label

