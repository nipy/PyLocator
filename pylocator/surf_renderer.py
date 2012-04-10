from __future__ import division
import sys, os
import vtk

import gtk
from gtk import gdk
from GtkGLExtVTKRenderWindowInteractor import GtkGLExtVTKRenderWindowInteractor
from marker_window_interactor import MarkerWindowInteractor

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu
from vtkutils import create_box_actor_around_marker

from events import EventHandler, UndoRegistry, Viewer
from markers import Marker
from shared import shared
from screenshot_taker import ScreenshotTaker


#class SurfRenderWindow(GtkGLExtVTKRenderWindowInteractor, Viewer):
class SurfRenderWindow(Viewer, ScreenshotTaker):
    """
    CLASS: SurfRenderWindow
    DESCR: Upper right frame in pylocator window
    """

    def __init__(self, imageData=None):
        #GtkGLExtVTKRenderWindowInteractor.__init__(self)
        ScreenshotTaker.__init__(self)
        EventHandler().attach(self)

        self.Initialize()
        self.Start()
        self.renderOn = True
        
        self.renderer = vtk.vtkRenderer()
        self.renWin = self.GetRenderWindow()

        #XXX XXX XXX my anaglyph stuff
        #self.renWin.SetStereoRender(1)
        #self.renWin.SetStereoTypeToRedBlue()

        self.renWin.AddRenderer(self.renderer)
        self.interactor = self.renWin.GetInteractor()
        self.renderer.SetBackground(0,0,0)
        self.textActors = {}
        self.boxes = {}
        
    def set_image_data(self, imageData):
        self.imageData = imageData
        if imageData is None: return
        center = imageData.GetCenter()
        spacing = imageData.GetSpacing()
        bounds = imageData.GetBounds()
        pos = center[0], center[1], center[2] - max(bounds)*2
        fpu = center, pos, (0,-1,0)
        self.set_camera(fpu)

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
                        
    def Render(self):
        if self.renderOn:
            GtkGLExtVTKRenderWindowInteractor.Render(self)
                
    def update_viewer(self, event, *args):
        if event=='render off':
            self.renderOn = 0
        elif event=='render on':
            self.renderOn = 1
            self.Render()
        elif event=='set image data':
            imageData = args[0]
            self.set_image_data(imageData)
            self.Render()
        elif event=='add marker':
            marker = args[0]
            self.add_marker(marker)
        elif event=='remove marker':
            marker = args[0]
            self.remove_marker(marker)
        elif event=='labels on':
            actors = self.textActors.values()
            for actor in actors:
                actor.VisibilityOn()
        elif event=='labels off':
            actors = self.textActors.values()
            for actor in actors:
                actor.VisibilityOff()
        elif event=='select marker':
            marker = args[0]
            actor = create_box_actor_around_marker(marker)
            if shared.debug: print "PlaneWidgetsXYZ.update_viewer(): self.renderer.AddActor(actor)"
            self.renderer.AddActor(actor)
            self.boxes[marker] = actor
        elif event=='unselect marker':
            marker = args[0]
            actor = self.boxes[marker]
            self.renderer.RemoveActor(actor)
        self.Render()

    def add_marker(self, marker):

        self.renderer.AddActor(marker)

        text = vtk.vtkVectorText()
        text.SetText(marker.get_label())
        textMapper = vtk.vtkPolyDataMapper()
        textMapper.SetInput(text.GetOutput())

        textActor = vtk.vtkFollower()
        textActor.SetMapper(textMapper)
        size = marker.get_size()
        textActor.SetScale(size, size, size)
        x,y,z = marker.get_center()
        textActor.SetPosition(x+size, y+size, z+size)
        textActor.SetCamera(self.renderer.GetActiveCamera())
        textActor.GetProperty().SetColor(marker.get_label_color())
        if EventHandler().get_labels_on():
            textActor.VisibilityOn()
        else:
            textActor.VisibilityOff()


        self.textActors[marker] = textActor
        self.renderer.AddActor(textActor)

    def remove_marker(self, marker):
        self.renderer.RemoveActor(marker)
        self.renderer.RemoveActor(self.textActors[marker])
        del self.textActors[marker]

    #def set_mouse1_to_screenshot(self):
    #    self.set_select_mode()
    #    cursor = gtk.gdk.Cursor (SCREENSHOT_CURSOR)
    #    self.pressHooks[1] = self.take_screenshot
    #    if self.window is not None:
    #        self.window.set_cursor (cursor)

    #def OnKeyPress(self, wid, event=None):
        #if (event.keyval == gdk.keyval_from_name("s") or
        #    event.keyval == gdk.keyval_from_name("S")):
        #    if shared.debug: print "KeyPress Screenshot"
        #    self.take_screenshot()
    #    return True
