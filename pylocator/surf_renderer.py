from __future__ import division
import sys, os
import vtk

import gtk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu
from vtkutils import create_box_actor_around_marker

from events import EventHandler
from markers import Marker
from shared import shared
from render_window import PyLocatorRenderWindow

class SurfRenderWindow(PyLocatorRenderWindow):
    """
    CLASS: SurfRenderWindow
    DESCR: Upper right frame in pylocator window
    """

    def __init__(self, imageData=None):
        PyLocatorRenderWindow.__init__(self)
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

    def set_labels_visibility(self, visible=True):
        if visible:
            actors = self.textActors.values()
            for actor in actors:
                actor.VisibilityOn()
        else:
            actors = self.textActors.values()
            for actor in actors:
                actor.VisibilityOff()

    def set_marker_selection(self, marker, select=True):
        if select:
            actor = create_box_actor_around_marker(marker)
            if shared.debug: print "PlaneWidgetsXYZ.update_viewer(): self.renderer.AddActor(actor)"
            self.renderer.AddActor(actor)
            self.boxes[marker] = actor
        else:
            actor = self.boxes[marker]
            self.renderer.RemoveActor(actor)

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
        
