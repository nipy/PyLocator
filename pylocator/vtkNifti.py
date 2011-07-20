import nifti
#from nifti import *
#from numpy import oldnumeric as Numeric
import vtk
import os
from vtk.util.vtkImageImportFromArray import vtkImageImportFromArray

class vtkNiftiImageReader(object):
    __defaultFilePattern=""

    def __init__(self):
        self.__vtkimport=vtk.vtkImageImport()
        self.__filePattern=self.__defaultFilePattern
        self.__data = None

    def SetDirectoryName(self,dir):
        self.__dirname=dir
        self.__filename=os.path.join(
                self.__dirname,self.__filePattern)

    def SetFilePrefix(self, dir):
        pass

    def SetFilePattern(self, pattern):
        self.__filePattern=pattern
        self.__filename=os.path.join(
                self.__dirname,self.__filePattern)

    def SetFileName(self, filename):
        self.__filename=filename
        #self.__nim=nifti.NiftiImage(self.__filename)
        #self.__data=self.__nim.asarray().astype("f")#.swapaxes(0,2)
        
    def Update(self):
        print "Loading ", self.__filename
        #read in the data after directory was set
        self.__nim=nifti.NiftiImage(self.__filename)
        self.__data=self.__nim.data.astype("f")
        self.__data_string = self.__data.tostring()
        #del self.__nim
        self.__vtkimport.CopyImportVoidPointer(self.__data_string,len(self.__data_string))
        self.__vtkimport.SetDataScalarTypeToFloat()
        self.__vtkimport.SetNumberOfScalarComponents(1)
        self.__vtkimport.SetDataExtent(0,self.__data.shape[0]-1,0,self.__data.shape[1]-1,0,self.__data.shape[2]-1)
        self.__vtkimport.SetWholeExtent(0,self.__data.shape[0]-1,0,self.__data.shape[1]-1,0,self.__data.shape[2]-1)
        self.SetDataSpacing(self.__nim.getVoxDims())#to reverse: [::-1]
        #XXX this is all not 100% right...
        #the data in array is z,y,x
        #getVoxDims returns x,y,z

    def GetWidth(self):
        return self.__nim.getVolumeExtent()[0]

    def GetHeight(self):
        return self.__nim.getVolumeExtent()[1]

    def GetDepth(self):
        return self.__nim.getVolumeExtent()[2]

    def SetDataSpacing(self, *args):
        if len(args)==1:
            try:
                a=(len(args[0])==3)
            except:
                self.__spacing=args+(0.0,0,0)
            else:
                self.__spacing=args[0] 
        elif len(args)==2:
            self.__spacing=args+(0.0,)
        elif len(args)<1:
            print "in vtkNifti.SetDataSpacing"
            print "negative number of dimensions not supported! ;-)"
        else:
            self.__spacing=args[:3]
        print args,self.__spacing
        self.__vtkimport.SetDataSpacing(self.__spacing)

    def GetDataSpacing(self):
        return self.__spacing
         
    def GetOutput(self):
        return self.__vtkimport.GetOutput()

    def GetFilename(self):
        print self.__filename
        return self.__filename

    def GetDataExtent(self):
        return self.__vtkimport.GetDataExtent()

    def GetQForm(self):
        return self.__nim.getQForm()
