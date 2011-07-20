import nifti
#from nifti import *
import Numeric
import vtk
import os
from vtk.util.vtkImageImportFromArray import vtkImageImportFromArray

class vtkNiftiImageReader(object):
    __defaultFilePattern=""

    def __init__(self):
        self.__vtkimport=vtkImageImportFromArray()
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
        self.__data=self.__nim.asarray().astype("f")
        #del self.__nim
        #XXX the conversion to Numeric could be very expensive
        #think about it...
        self.__vtkimport.SetArray(Numeric.array(self.__data))
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
