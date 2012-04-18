"""Define vtkActors for use in PyLocatorRenderWindow"""

import math
import vtk
import uuid

import numpy as n

class Marker(vtk.vtkActor):
    """
    CLASS: Marker
    DESCR: Represents, e.g., an individual grid location as a vtk sphere
    """
    def __init__(self, xyz, radius, rgb = None, uuid_=None):
        if rgb is None: 
            rgb = (0, 0, 1)

        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(radius)
        res = 20
        self.sphere.SetThetaResolution(res)
        self.sphere.SetPhiResolution(res)
        self.sphere.SetCenter(xyz)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(self.sphere.GetOutput())
        mapper.ImmediateModeRenderingOn()
        
        self.SetMapper(mapper)

        self.GetProperty().SetColor( rgb )

        self.set_lighting()

        self.label = ''
        self.label_color = (1, 1, 0.5)

        #create ID
        if not uuid_:
            self.uuid = uuid.uuid1()
        else:
            self.uuid = uuid_

    def set_lighting(self):
        """Set the lighting of the marker actor"""
        prop = self.GetProperty()
        prop.SetAmbient(0.)
        prop.SetDiffuse(0.)
        prop.SetSpecular(1.0)

    def contains(self, xyz):
        """Return true if point xyz is in the marker"""
        if xyz is None: return 0
        d = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(
            self.sphere.GetCenter(), xyz))
        #print 'locs', xyz, self.sphere.GetCenter()
        if d < self.sphere.GetRadius():  return 1
        else: return 0

    def get_source(self):
        return self.sphere

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def get_label_color(self):
        return self.label_color

    def set_label_color(self, color):
        self.label_color = color

    def get_center(self):
        return self.sphere.GetCenter()

    def set_center(self, center):
        self.sphere.SetCenter(center)

    def get_size(self):
        return self.sphere.GetRadius()

    def set_size(self, s):
        return self.sphere.SetRadius(s)

    def set_color(self, color):
        print "Marker.GetProperty().SetColor(", color, ")"
        self.GetProperty().SetColor( color )

    def get_color(self):
        return self.GetProperty().GetColor()

    def deep_copy(self):
        m = Marker(xyz=self.sphere.GetCenter(),
                   radius=self.sphere.GetRadius(),
                   rgb=self.GetProperty().GetColor(),
                   uuid_=self.uuid)
        m.set_label(self.get_label())
        return m

    def to_string(self):
        r,g,b = self.get_color()
        x,y,z = self.get_center()
        radius = self.get_size()
        label = self.get_label()
        s = label + ',' + ','.join(map(str, (x,y,z,radius,r,g,b)))
        return s

    def from_string(s):
        #todo; use csv module
        vals = s.replace('"', '').split(',')
        label = vals[0]
        x,y,z,radius,r,g,b = map(float, vals[1:])
        marker = Marker(xyz=(x,y,z), radius=radius, rgb=(r,g,b))
        marker.set_label(label)
        return marker

    def get_name_num(self):
        label = self.get_label()
        tup = label.split()
        if len(tup)!=2: return label, 0

        name, num = tup
        try: num = int(num)
        except ValueError: return label, 0
        except TypeError: return label, 0
        else: return name, num

    color = property(get_color, set_color)

class RingActor(vtk.vtkActor):
    def __init__(self, marker, planeWidget,
                 transform=None, lineWidth=1):
    
        self.lineWidth=lineWidth
        self.marker = marker
        self.markerSource = marker.get_source()
        self.planeWidget = planeWidget
        self.transform = transform

        self.implicitPlane = vtk.vtkPlane()
        self.ringEdges = vtk.vtkCutter()
        self.ringStrips = vtk.vtkStripper()
        self.ringPoly = vtk.vtkPolyData()
        self.ringMapper = vtk.vtkPolyDataMapper()

        self.ringEdges.SetInput(self.markerSource.GetOutput())
        self.implicitPlane.SetNormal(self.planeWidget.GetNormal())
        self.implicitPlane.SetOrigin(self.planeWidget.GetOrigin())

        #print 'implicit plane', self.implicitPlane
        self.ringEdges.SetCutFunction(self.implicitPlane)
        self.ringEdges.GenerateCutScalarsOff()
        self.ringEdges.SetValue(0, 0.0)
        self.ringStrips.SetInput(self.ringEdges.GetOutput())
        self.ringStrips.Update()
        self.ringPoly.SetPoints(self.ringStrips.GetOutput().GetPoints())
        self.ringPoly.SetPolys(self.ringStrips.GetOutput().GetLines())
        self.ringMapper.SetInput(self.ringPoly)
        self.SetMapper(self.ringMapper)

        self.lineProperty = self.GetProperty()
        self.lineProperty.SetRepresentationToWireframe()
        self.lineProperty.SetAmbient(1.0)
        self.lineProperty.SetColor(self.marker.get_color())
        self.lineProperty.SetLineWidth(lineWidth)

        self.SetProperty(self.lineProperty)
        self.VisibilityOff()

        if transform is not None:
            self.filter = vtk.vtkTransformPolyDataFilter()
            self.filter.SetTransform(transform)
        else:
            self.filter = None
        self.update()

        
    def update(self, *args):
        # side effects update the ring poly
        if not self.is_visible(): return 0
        
        self.lineProperty.SetColor(self.marker.get_color())
        
        if self.filter is not None:
            self.filter.SetInput(self.ringPoly)
            self.ringMapper.SetInput(self.filter.GetOutput())
        else:
            self.ringMapper.SetInput(self.ringPoly)
        self.ringMapper.Update()
        self.VisibilityOn()
        return 1
        
    def get_marker(self):
        return self.marker

    def set_line_width(self, w):
        self.lineWidth = w
        self.lineProperty.SetLineWidth(w)

    def get_line_width(self, w):
        return self.lineWidth

    def set_selected(self, selected=False):
        if selected:
            self.lineProperty.SetLineWidth(self.lineWidth*5)
        else:
            self.lineProperty.SetLineWidth(self.lineWidth)
        self.update()

    def is_visible(self):
        # side effects update the ring poly; so kill me
        self.implicitPlane.SetNormal(self.planeWidget.GetNormal())
        self.implicitPlane.SetOrigin(self.planeWidget.GetOrigin())
        self.ringStrips.Update()
        self.ringPoly.SetPoints(self.ringStrips.GetOutput().GetPoints())
        self.ringPoly.SetPolys(self.ringStrips.GetOutput().GetLines())
        self.ringPoly.Update()
        return self.ringPoly.GetNumberOfPolys()

