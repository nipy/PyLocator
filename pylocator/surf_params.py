from __future__ import division
import uuid
import vtk
import gtk
from gtkutils import ProgressBarDialog
from events import EventHandler
from connect_filter import ConnectFilter
from decimate_filter import DecimateFilter
from colors import colorSeq, gdkColor2tuple

class SurfParams(object):
    label = "Surface"
    colorName, color_  = colorSeq[0]
    intensity     = 80.
    _opacity = 1.0

    useConnect    = True
    useDecimate   = False

    def __init__(self, imageData, intensity, color=None):
        self._uuid = uuid.uuid1()
        if intensity!=None:
            self.intensity = intensity
        if color==None:
            color=self.color_
        self.set_color(color)

        self.connect = ConnectFilter()
        self.deci = DecimateFilter()
        self.marchingCubes = vtk.vtkMarchingCubes()
        self.marchingCubes.SetInput(imageData)

        self.output = vtk.vtkPassThrough()

        self.prog = ProgressBarDialog(
            title='Rendering surface %s' % self.label,
            parent=None,
            msg='Marching cubes ....',
            size=(300,40),
        )
        self.prog.set_modal(True)

        def start(o, event):
            self.prog.show()
            while gtk.events_pending(): gtk.main_iteration()


        def progress(o, event):
            val = o.GetProgress()
            self.prog.bar.set_fraction(val)            
            while gtk.events_pending(): gtk.main_iteration()
            
        def end(o, event):
            self.prog.hide()
            while gtk.events_pending(): gtk.main_iteration()

        self.marchingCubes.AddObserver('StartEvent', start)
        self.marchingCubes.AddObserver('ProgressEvent', progress)
        self.marchingCubes.AddObserver('EndEvent', end)
        
        self.update_pipeline()

        self.notify_add_surface(self.output)


    def update_pipeline(self):
        pipe = self.marchingCubes

        if self.useConnect:
            self.connect.SetInputConnection( pipe.GetOutputPort())
            pipe = self.connect

        if self.useDecimate:
            self.deci.SetInputConnection( pipe.GetOutputPort())
            pipe = self.deci

        self.output.SetInputConnection( pipe.GetOutputPort() )
        self.update_properties()

    def notify_add_surface(self, pipe):
        EventHandler().notify("add surface", self._uuid, pipe, self._color)

    def notify_remove_surface(self):
        EventHandler().notify("remove surface", self._uuid)

    def notify_color_surface(self, color):
        EventHandler().notify("color surface", self._uuid, color)

    def notify_change_surface_opacity(self, opacity):
        EventHandler().notify("change surface opacity", self._uuid, opacity)

    def update_properties(self):
        self.marchingCubes.SetValue(0, self.intensity)
        self.notify_color_surface(self.color)

        if self.useConnect:  self.connect.update()
        if self.useDecimate: self.deci.update()

    def update_viewer(self, event, *args):
        if event=='set image data':
            imageData = args[0]
            self.set_image_data(imageData)       

    def __del__(self):
        self.notify_remove_surface()

    def set_color(self,color, color_name=""):
        #print color, type(color)
        self.colorName = color_name
        if type(color)==gtk.gdk.Color:
            self._color = gdkColor2tuple(color)
        else:
            self._color = color
        self.notify_color_surface(self._color)

    def get_color(self):
        return self._color

    def set_opacity(self,opacity):
        self._opacity = opacity
        self.notify_change_surface_opacity(self._opacity)

    def get_opacity(self):
        return self._opacity

    def get_uuid(self):
        return self._uuid

    color = property(get_color,set_color)
    opacity = property(get_opacity,set_opacity)
    uuid = property(get_uuid)

    def destroy(self):
        self.notify_remove_surface()
