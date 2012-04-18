from __future__ import division
import vtk
from events import EventHandler
from surf_params import SurfParams


class RoiParams(SurfParams):
    intensity = 0.5

    def __init__(self, imageData, color=None):
        if color==None:
            color = (0.,0.,1.)
        SurfParams.__init__(self, imageData, self.intensity, color)

    def set_lighting(self):
        surf_prop = self.isoActor.GetProperty()
        surf_prop.SetAmbient(.2)
        surf_prop.SetDiffuse(.3)
        surf_prop.SetSpecular(.5)

    def notify_add_surface(self, pipe):
        EventHandler().notify("add roi", self._uuid, pipe, self._color)

    def notify_remove_surface(self):
        EventHandler().notify("remove roi", self._uuid)

    def notify_color_surface(self, color):
        EventHandler().notify("color roi", self._uuid, color)

    def notify_change_surface_opacity(self, opacity):
        EventHandler().notify("change roi opacity", self._uuid, opacity)

class RoiEdgeActor(vtk.vtkActor):
    def __init__(self, roi_pipe, color, planeWidget, transform=None, lineWidth=2):
        self.roiPipe = roi_pipe
        self._color = color
        self.planeWidget = planeWidget
        self.transform = transform
        self._line_width=lineWidth

        self.__create_and_set_mapper()

        lp = self.GetProperty()
        lp.SetRepresentationToWireframe()
        lp.SetAmbient(1.0)
        lp.SetColor(self._color)
        lp.SetLineWidth(lineWidth)
        self.SetProperty(lp)
        self.VisibilityOff()

        if transform is not None:
            self.filter = vtk.vtkTransformPolyDataFilter()
            self.filter.SetTransform(transform)
        else:
            self.filter = None

        self.update()

    def __create_and_set_mapper(self):
        self.implicitPlane = vtk.vtkPlane()
        self.edges = vtk.vtkCutter()
        self.strips = vtk.vtkStripper()
        self.poly = vtk.vtkPolyData()
        self.mapper = vtk.vtkPolyDataMapper()

        self.edges.SetInputConnection(self.roiPipe.GetOutputPort())
        self.implicitPlane.SetNormal(self.planeWidget.GetNormal())
        self.implicitPlane.SetOrigin(self.planeWidget.GetOrigin())

        self.edges.SetCutFunction(self.implicitPlane)
        self.edges.GenerateCutScalarsOff()
        self.edges.SetValue(0, 0.0)
        self.strips.SetInputConnection(self.edges.GetOutputPort())
        self.strips.Update()
        self.poly.SetPoints(self.strips.GetOutput().GetPoints())
        self.poly.SetPolys(self.strips.GetOutput().GetLines())
        self.mapper.SetInput(self.poly)
        self.mapper.ScalarVisibilityOff()
        self.SetMapper(self.mapper)

    def update(self, *args):
        # side effects update the poly
        if not self.is_visible(): return 0
        
        if self.filter is not None:
            self.filter.SetInput(self.poly)
            self.mapper.SetInputConnection(self.filter.GetOutputPort())
        else:
            self.mapper.SetInput(self.poly)
        self.mapper.Update()
        self.VisibilityOn()
        return 1
        
    def get_roi_param(self):
        return self.marker

    def get_line_width(self):
        return self._line_width

    def set_line_width(self, w):
        self._line_width = w
        self.GetProperty().SetLineWidth(w)

    line_width = property(get_line_width, set_line_width)

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = color
        self.GetProperty().SetColor(color)

    color = property(get_color, set_color)


    def is_visible(self):
        # side effects update the poly; so kill me
        self.implicitPlane.SetNormal(self.planeWidget.GetNormal())
        self.implicitPlane.SetOrigin(self.planeWidget.GetOrigin())
        self.strips.Update()
        self.poly.SetPoints(self.strips.GetOutput().GetPoints())
        self.poly.SetPolys(self.strips.GetOutput().GetLines())
        self.poly.Update()
        return self.poly.GetNumberOfPolys()

    def silly_hack(self, *args):
        # vtk strips my attributes if I don't register a func as an observer
        pass

