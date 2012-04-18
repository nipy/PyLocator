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
from render_window import PyLocatorRenderWindow, ThreeDimRenderWindow

class SurfRenderWindow(ThreeDimRenderWindow, PyLocatorRenderWindow):

    def __init__(self, imageData=None):
        PyLocatorRenderWindow.__init__(self)
        ThreeDimRenderWindow.__init__(self)
        self.surface_actors = {}

    def set_image_data(self, imageData):
        self.imageData = imageData
        if imageData is None: return
        center = imageData.GetCenter()
        spacing = imageData.GetSpacing()
        bounds = imageData.GetBounds()
        pos = center[0], center[1], center[2] - max(bounds)*2
        fpu = center, pos, (0,-1,0)
        self.set_camera(fpu)
        self.camera = self.renderer.GetActiveCamera()

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

    def add_surface(self, uuid, pipe, color):
        isoActor = self._create_actor(pipe)
        isoActor.GetProperty().SetColor(color)
        self._set_surface_lighting(isoActor)
        self.surface_actors[uuid] = isoActor
        
    def remove_surface(self, uuid):
        actor = self.__get_surface_actor(uuid)
        if actor:
            self.renderer.RemoveActor(actor)
            del self.surface_actors[uuid]

    def color_surface(self, uuid, color):
        actor = self.__get_surface_actor(uuid)
        if actor:
            actor.GetProperty().SetColor(color)

    def change_surface_opacity(self, uuid, opacity):
        actor = self.__get_surface_actor(uuid)
        if actor:
            actor.GetProperty().SetOpacity(opacity)

    def __get_surface_actor(self, uuid):
        if not self.surface_actors.has_key(uuid):
            return
        return self.surface_actors[uuid]

    def update_viewer(self, event, *args):
        PyLocatorRenderWindow.update_viewer(self, event, *args)
        self.Render()

