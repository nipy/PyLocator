import gtk
import vtk
from GtkGLExtVTKRenderWindowInteractor import GtkGLExtVTKRenderWindowInteractor
from events import EventHandler
from gtkutils import error_msg
from vtkutils import create_box_actor_around_marker

from shared import shared


INTERACT_CURSOR, MOVE_CURSOR, COLOR_CURSOR, SELECT_CURSOR, DELETE_CURSOR, LABEL_CURSOR, SCREENSHOT_CURSOR = gtk.gdk.ARROW, gtk.gdk.HAND2, gtk.gdk.SPRAYCAN, gtk.gdk.TCROSS, gtk.gdk.X_CURSOR, gtk.gdk.PENCIL, gtk.gdk.ICON

class PyLocatorRenderWindow(GtkGLExtVTKRenderWindowInteractor):
    background = (0.,0.,0.)

    def __init__(self,*args):
        GtkGLExtVTKRenderWindowInteractor.__init__(self,*args)
        self.screenshot_button_label = "_render window_"
        self.roi_actors = {}

        EventHandler().attach(self)
        self.interactButtons = (1,2,3)
        self.renderOn = 1
        self.Initialize()
        self.Start()

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(self.background)
        self.renWin = self.GetRenderWindow()
        self.renWin.AddRenderer(self.renderer)
        self.interactor = self.renWin.GetInteractor()

        self.camera_default_fpu = None
        self.camera = self.renderer.GetActiveCamera()

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

    def set_image_data(self, image_data):
        pass

    def add_marker(self, marker):
        pass

    def remove_marker(self, marker):
        pass

    def set_labels_visibility(self, visible=True):
        pass

    def set_marker_selection(self, marker, select=True):
        pass

    def add_surface(self, uuid, pipe, color):
        pass

    def remove_surface(self, uuid):
        pass

    def color_surface(self, uuid, color):
        pass

    def change_surface_opacity(self, uuid, opactiy):
        pass

    def add_roi(self, uuid, pipe, color):
        pass

    def remove_roi(self, uuid):
        pass

    def color_roi(self, uuid, color):
        pass

    def change_roi_opacity(self, uuid, opactiy):
        pass

    def _get_roi_actor(self, uuid):
        if not self.roi_actors.has_key(uuid):
            return
        return self.roi_actors[uuid]

    def update_viewer(self, event, *args):
        if event=='render off':
            self.renderOn = 0
        elif event=='render on':
            self.renderOn = 1
            self.Render()
        elif event=='render now':
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
            self.set_labels_visibility(True)
        elif event=='labels off':
            self.set_labels_visibility(False)
        elif event=='select marker':
            marker = args[0]
            self.set_marker_selection(marker, True)
        elif event=='unselect marker':
            marker = args[0]
            self.set_marker_selection(marker, False)
        elif event=='add surface':
            uuid, pipe, color = args
            self.add_surface(uuid, pipe, color)
        elif event=='remove surface':
            uuid = args[0]
            self.remove_surface(uuid)
        elif event=='color surface':
            uuid, color = args
            self.color_surface(uuid, color)
        elif event=='add roi':
            uuid, pipe, color = args
            self.add_roi(uuid, pipe, color)
        elif event=='remove roi':
            uuid = args[0]
            self.remove_roi(uuid)
        elif event=='color roi':
            uuid, color = args
            self.color_roi(uuid, color)
        elif event=='change surface opacity':
            uuid, opacity = args
            self.change_surface_opacity(uuid, opacity)
        elif event=='change roi opacity':
            uuid, opacity = args
            self.change_roi_opacity(uuid, opacity)
        self.Render()

class ThreeDimRenderWindow(object):
    textActors = {}

    def __init__(self):
        self.boxes = {}

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
        textActor.SetCamera(self.camera)
        textActor.GetProperty().SetColor(marker.get_label_color())
        if EventHandler().get_labels_on():
            if shared.debug: print "VisibilityOn"
            textActor.VisibilityOn()
        else:
            if shared.debug: print "VisibilityOff"
            textActor.VisibilityOff()
        self.textActors[marker] = textActor
        self.renderer.AddActor(textActor)

    def remove_marker(self, marker):
        self.renderer.RemoveActor(marker)
        try:
            self.renderer.RemoveActor(self.textActors[marker])
            del self.textActors[marker]
        except KeyError:
            pass

    def set_marker_selection(self, marker, select=True):
        if select:
            actor = create_box_actor_around_marker(marker)
            if shared.debug: print "PlaneWidgetsXYZ.update_viewer(): self.renderer.AddActor(actor)"
            self.renderer.AddActor(actor)
            self.boxes[marker] = actor
        else:
            actor = self.boxes[marker]
            self.renderer.RemoveActor(actor)

    def add_roi(self, uuid, pipe, color):
        isoActor = self._create_actor(pipe)
        isoActor.GetProperty().SetColor(color)
        self._set_roi_lighting(isoActor)
        self.roi_actors[uuid] = isoActor

    def remove_roi(self, uuid):
        actor = self._get_roi_actor(uuid)
        if actor:
            self.renderer.RemoveActor(actor)
            del self.roi_actors[uuid]

    def color_roi(self, uuid, color):
        actor = self._get_roi_actor(uuid)
        if actor:
            p = actor.GetProperty()
            p.SetColor(color)

    def change_roi_opacity(self, uuid, opacity):
        actor = self._get_roi_actor(uuid)
        if actor:
            actor.GetProperty().SetOpacity(opacity)
        return self.roi_actors[uuid]

    def _create_actor(self,pipe):
        isoMapper = vtk.vtkPolyDataMapper()
        isoMapper.SetInput(pipe.GetOutput())
        isoMapper.ScalarVisibilityOff()

        isoActor = vtk.vtkActor()
        isoActor.SetMapper(isoMapper)
        self.renderer.AddActor(isoActor)
        return isoActor

    def _set_roi_lighting(self, isoActor):
        surf_prop = isoActor.GetProperty()
        surf_prop.SetAmbient(.2)
        surf_prop.SetDiffuse(.3)
        surf_prop.SetSpecular(.5)

    def _set_surface_lighting(self, isoActor):
        surf_prop = isoActor.GetProperty()
        surf_prop.SetAmbient(.2)
        surf_prop.SetDiffuse(.3)
        surf_prop.SetSpecular(.5)

