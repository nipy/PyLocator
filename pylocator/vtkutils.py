import vtk
import numpy as np

def vtkmatrix4x4_to_array(vtkmat):
    scipy_array = np.zeros((4,4), 'd')
    for i in range(0,4):
        for j in range(0,4):
            scipy_array[i,j] = mat.GetElement(i,j)
    return scipy_array 

def array_to_vtkmatrix4x4(scipy_array):
    mat = vtk.vtkMatrix4x4()
    for i in range(0,4):
        for j in range(0,4):
            mat.SetElement(i,j, scipy_array[i,j])
    return mat

def create_box_actor_around_marker(marker):
    boxSource = vtk.vtkCubeSource()
    boxSource.SetBounds(marker.GetBounds())
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInput(boxSource.GetOutput())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor( marker.get_color() )
    actor.GetProperty().SetRepresentationToWireframe()
    actor.GetProperty().SetLineWidth(2.0)
    return actor
