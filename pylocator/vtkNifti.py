from nibabel import load
#from numpy import oldnumeric as Numeric
import numpy as np
import vtk
from shared import shared
from vtkutils import array_to_vtkmatrix4x4

#from vtk.util.vtkImageImportFromArray import vtkImageImportFromArray

class vtkNiftiImageReader(object):
    __defaultFilePattern=""

    def __init__(self):
        self.__vtkimport=vtk.vtkImageImport()
        self.__vtkimport.SetDataScalarTypeToFloat()
        self.__vtkimport.SetNumberOfScalarComponents(1)
        self.__filePattern=self.__defaultFilePattern
        self.__data = None
        self._irs = vtk.vtkImageReslice()

    def SetFileName(self, filename):
        self.__filename=filename
        
    def Update(self):
        if shared.debug: print "Loading ", self.__filename
        self.__nim=load(self.__filename)
        if shared.debug: print self.__nim
        self.__data=self.__nim.get_data().astype("f").swapaxes(0,2)
        #self.__vtkimport.SetDataExtent(0,self.__data.shape[2]-1,0,self.__data.shape[1]-1,0,self.__data.shape[0]-1)
        self.__vtkimport.SetWholeExtent(0,self.__data.shape[2]-1,0,self.__data.shape[1]-1,0,self.__data.shape[0]-1)
        self.__vtkimport.SetDataExtentToWholeExtent()
        voxdim = self.__nim.get_header()['pixdim'][:3].copy()
        #Export data as string
        self.__data_string = self.__data.tostring()
        if shared.debug: print voxdim
        self.__vtkimport.SetDataSpacing((1.,1.,1.))#to reverse: [::-1]
        self.__vtkimport.CopyImportVoidPointer(self.__data_string,len(self.__data_string))
        self.__vtkimport.UpdateWholeExtent()

        imgData1 = self.__vtkimport.GetOutput()
        imgData1.SetExtent(self.__vtkimport.GetDataExtent())
        imgData1.SetOrigin((0,0,0))
        imgData1.SetSpacing(1.,1.,1.)
        #print imgData1
        #print self._irs
        #self._irs.SetInputConnection(self.__vtkimport.GetOutputPort())
        self._irs.SetInput(imgData1)
        #print self._irs
        self._irs.SetInterpolationModeToCubic()
        #self._irs.AutoCropOutputOn()
        
        
        affine = array_to_vtkmatrix4x4(self.__nim.get_affine())
        if shared.debug: print self._irs.GetResliceAxesOrigin()
        self._irs.SetResliceAxes(affine)
        if shared.debug: print self._irs.GetResliceAxesOrigin()
        m2t = vtk.vtkMatrixToLinearTransform()
        m2t.SetInput(affine.Invert())
        self._irs.TransformInputSamplingOff()
        self._irs.SetResliceTransform(m2t.MakeTransform())
        #self._irs.SetResliceAxesOrigin((0.,0.,0.)) #self.__vtkimport.GetOutput().GetOrigin())
        #print self.__vtkimport.GetOutput().GetBounds()
        #print self._irs.GetOutput().GetBounds()

        if shared.debug: print voxdim, self._irs.GetOutputSpacing()
        self._irs.SetOutputSpacing(abs(voxdim))
        if shared.debug: print self._irs.GetOutputSpacing()
        #print self._irs.GetOutputOrigin()
        #self._irs.SetOutputOrigin((0,0,0))
        # print self._irs.GetOutputOrigin()

        #m2t_i.DeepCopy(m2t);
        #m2t_i = affine_i.Invert();
        #m2t_i.MultiplyPoint(); 
        #self._irs.SetOutputOrigin(self.__nim.get_affine()[:3,-1])
        
        #self._irs.SetOutputExtent(self.__vtkimport.GetDataExtent())
        self._irs.AutoCropOutputOn()

        self._irs.Update()


    def GetWidth(self):
        return self._irs.GetOutput().GetBounds()[0:2]

    def GetHeight(self):
        return self._irs.GetOutput().GetBounds()[2:4]

    def GetDepth(self):
        return self._irs.GetOutput().GetBouds()[4:]

    def GetDataSpacing(self):
        if shared.debug: print self.__spacing, "*******************"
        return self._irs.GetOutput().GetSpacing()
         
    def GetOutput(self):
        #return self.__vtkimport.GetOutput()
        #imageData = self._irs.GetOutput()
        #return imageData
        return self._irs.GetOutput()

    def GetFilename(self):
        if shared.debug: print self.__filename
        return self.__filename

    def GetDataExtent(self):
        return self._irs.GetOutput().GetDataExtent()

    def GetBounds(self):
        return self._irs.GetOutput().GetBounds()

    def GetQForm(self):
        return self.__nim.get_affine()

    @property
    def nifti_voxdim(self):
        return self.__nim.get_header()['pixdim'][:3]

    @property
    def shape(self):
        return self.__nim.shape

    @property
    def min(self):
        if self.__data!=None:
            return self.__data.min()

    @property
    def max(self):
        if self.__data!=None:
            return self.__data.max()

    @property
    def median(self):
        d = self.__data
        if d!=None:
            return np.median(d[d!=0])

if __name__ == "__main__":
    reader = vtkNiftiImageReader()
    reader.SetFileName("/home/thorsten/Dokumente/pylocator-examples/Can7/mri/post2std_brain.nii.gz")
    reader.Update()
    print reader._irs
    print reader.GetOutput()
