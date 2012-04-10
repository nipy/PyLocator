from __future__ import division
import sys, os
import vtk

import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu

from events import EventHandler, UndoRegistry, Viewer
from markers import Marker
from shared import shared

from connect_filter import ConnectFilter
from decimate_filter import DecimateFilter

from colors import colorSeq, gdkColor2tuple

class SurfParams(Viewer):
    """
    CLASS: SurfParams
    DESCR:

      Public attrs:
    
      color_      # a normed rgb
      intensity   # intensity to segment on
      label       # name of segment
      useConnect  # boolean, whether to use ConnectFilter
      useDecimate # boolean, whether to use DecimateFilter
      connect     # a ConnectFilter or None
      deci        # a DecimateFilter or None
      imageData   # default None
    """

    label, color_  = colorSeq[0]
    intensity     = 80.

    useConnect    = True
    useDecimate   = False

    def __init__(self, renderers, interactor):

        self._color = SurfParams.color_
        self._opacity = 1.0

        self.connect = ConnectFilter()
        self.deci = DecimateFilter()
        self.marchingCubes = vtk.vtkMarchingCubes()

        self.prog = ProgressBarDialog(
            title='Rendering surface %s' % self.label,
            parent=None,
            msg='Marching cubes ....',
            size=(300,40),
                                 )
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
        #Make sure we have a list ef renderer (even if length 1)
        try:
            renderers = list(renderers)
        except TypeError, te:
            renderers = [renderers]
        self.renderers = renderers
        self.interactor = interactor
        self.isoActor = None
        
        self.update_pipeline()

    def update_pipeline(self):

        if self.isoActor is not None:
            for renderer in self.renderers:
                renderer.RemoveActor(self.isoActor)

        
        
        pipe = self.marchingCubes


        if self.useConnect:
            self.connect.SetInput( pipe.GetOutput())
            pipe = self.connect

        if self.useDecimate:
            self.deci.SetInput( pipe.GetOutput())
            pipe = self.deci

        if 0:
            plane = vtk.vtkPlane()
            clipper = vtk.vtkClipPolyData()
            polyData = pipe.GetOutput()

            clipper.SetInput(polyData)
            clipper.SetClipFunction(plane)
            clipper.InsideOutOff()
            pipe = clipper

            def callback(pw, event):
                pw.GetPlane(plane)
                self.interactor.Render()
            self.planeWidget = vtk.vtkImplicitPlaneWidget()
            self.planeWidget.SetInteractor(self.interactor)
            self.planeWidget.On()
            self.planeWidget.SetPlaceFactor(1.0)
            self.planeWidget.SetInput(polyData)
            self.planeWidget.PlaceWidget()
            self.planeWidget.AddObserver("InteractionEvent", callback)
        
        
        self.isoMapper = vtk.vtkPolyDataMapper()
        self.isoMapper.SetInput(pipe.GetOutput())
        self.isoMapper.ScalarVisibilityOff()

        self.isoActor = vtk.vtkActor()
        self.isoActor.SetMapper(self.isoMapper)
        self.set_lighting()
        for renderer in self.renderers:
            renderer.AddActor(self.isoActor)
        self.update_properties()

    def set_lighting(self):
        #self.isoActor.GetProperty().SetSpecular(1.0)
        pass

    def set_image_data(self, imageData):
        print "SurfParams.set_image_data(", imageData,")"
        self.marchingCubes.SetInput(imageData)
        x1,x2,y1,y2,z1,z2 = imageData.GetExtent()
        sx, sy, sz = imageData.GetSpacing()
        if 0:
            self.planeWidget.PlaceWidget((x1*sx, x2*sx, y1*sy, y2*sy, z1*sz, z2*sz))

    def update_properties(self):
        self.marchingCubes.SetValue(0, self.intensity)
        self.isoActor.GetProperty().SetColor(self.color)

        if self.useConnect:  self.connect.update()
        if self.useDecimate: self.deci.update()

    def update_viewer(self, event, *args):
        if event=='set image data':
            imageData = args[0]
            self.set_image_data(imageData)       

    def __del__(self):
        if self.isoActor is not None:
            for renderer in self.renderers:
                renderer.RemoveActor(self.isoActor)

    def set_color(self,color):
        print color, type(color)
        if type(color)==gtk.gdk.Color:
            print "adjusting color"
            self._color = gdkColor2tuple(color)
            print self._color
        else:
            self._color = color
        self.isoActor.GetProperty().SetColor(self._color)
        for renderer in self.renderers:
            renderer.Render()

    def get_color(self):
        return self._color

    def set_opacity(self,opacity):
        self._opacity = opacity
        self.isoActor.GetProperty().SetOpacity(self._opacity)

    def get_opacity(self):
        return self._opacity

    color = property(get_color,set_color)
    opacity = property(get_opacity,set_opacity)

    def destroy(self):
        if self.isoActor is not None:
            for renderer in self.renderers:
                renderer.RemoveActor(self.isoActor)
