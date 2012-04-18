from __future__ import division
import vtk
import gtk
from gtkutils import error_msg

from events import EventHandler
from markers import Marker
from shared import shared
from render_window import PyLocatorRenderWindow, ThreeDimRenderWindow

class SurfRenderWindow(ThreeDimRenderWindow, PyLocatorRenderWindow):
    picker_id = None

    def __init__(self, imageData=None):
        PyLocatorRenderWindow.__init__(self)
        ThreeDimRenderWindow.__init__(self)
        self.surface_actors = {}
        self.AddObserver('KeyPressEvent', self.key_press)

    def set_image_data(self, imageData):
        self.imageData = imageData
        if imageData is None: return
        center = imageData.GetCenter()
        #spacing = imageData.GetSpacing()
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

    def set_picker_surface(self, uuid):
        self.picker_id = uuid

    def add_surface(self, uuid, pipe, color):
        isoActor = self._create_actor(pipe)
        isoActor.GetProperty().SetColor(color)
        self._set_surface_lighting(isoActor)
        self.surface_actors[uuid] = isoActor
        if not self.picker_id:
            self.picker_id = uuid
        
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
        if event=='set picker surface':
            self.set_picker_surface(args[0])
        self.Render()

    def key_press(self, interactor, event):
        if shared.debug: print "key press event in SurfRenderWindow"
        key = interactor.GetKeySym()
        sas = self.surface_actors

        def checkPickerId():
            if not self.picker_id:
                error_msg('Cannot insert marker. Choose surface first.')
                return False
            return True

        if key.lower()=='q': #hehehe
            gtk.main_quit()
        if key.lower()=='i':
            if not checkPickerId():
                return
            if shared.debug: print "Inserting Marker"
            x,y = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.PickFromListOn()
            actor = self.__get_surface_actor(self.picker_id)
            if actor==None: return
            picker.AddPickList(actor)
            picker.SetTolerance(0.005)
            picker.Pick(x, y, 0, self.renderer)
            points = picker.GetPickedPositions()
            numPoints = points.GetNumberOfPoints()
            if numPoints<1: return
            pnt = points.GetPoint(0)

            marker = Marker(xyz=pnt,
                            rgb=EventHandler().get_default_color(),
                            radius=shared.ratio*shared.marker_size)
            EventHandler().add_marker(marker)
        elif key.lower()=='x':
            #if not checkPickerIdx():
            #    return
            x,y = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.PickFromListOn()
            for actor in sas:
                picker.AddPickList(actor)
            picker.SetTolerance(0.01)
            picker.Pick(x, y, 0, self.renderer)
            cellId = picker.GetCellId()
            if cellId==-1:
                pass
            else:
                o = self.paramd.values()[0]
                o.remove.RemoveCell(cellId)
                interactor.Render()
