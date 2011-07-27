import nibabel
#import nifti
#from nifti import *
#from numpy import oldnumeric as Numeric
import numpy as np
import vtk
import os
from shared import shared

#from vtk.util.vtkImageImportFromArray import vtkImageImportFromArray

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
        if shared.debug: print "Loading ", self.__filename
        #read in the data after directory was set
        #self.__nim=nifti.NiftiImage(self.__filename)
        self.__nim=nibabel.load(self.__filename)
        self.__data=self.__nim.get_data().astype("f").swapaxes(0,2)
        #self.__vtkimport.SetDataExtent(0,self.__data.shape[2]-1,0,self.__data.shape[1]-1,0,self.__data.shape[0]-1)
        self.__vtkimport.SetWholeExtent(0,self.__data.shape[2]-1,0,self.__data.shape[1]-1,0,self.__data.shape[0]-1)
        self.__vtkimport.SetDataExtentToWholeExtent()
        voxdim = self.__nim.get_header()['pixdim'][:3].copy()
        #flip all axes with negative spacing, adjust voxdim
        voxdim_signs = [1,1,1]
        for i in range(3):
            if voxdim[i]<0:
                #if shared.debug: print "FLIPPING axis no.", i
                voxdim[i]*=-1
                voxdim_signs[i]*=-1
                #if shared.debug: print "Example before:", self.__data[60,100,60]
                self.__data = nibabel.orientations.flip_axis(self.__data,i)
                #if shared.debug: print "Example after:", self.__data[60,100,60]
        #if shared.debug: print "Example after loop:", self.__data[60,100,60]
        #Export data as string
        self.__data_string = self.__data.tostring()
        #if shared.debug: print "Example from string:", np.fromstring(self.__data_string,"f").reshape(self.__data.shape)[60,100,60]
        if shared.debug: print voxdim
        self.SetDataSpacing(voxdim)#to reverse: [::-1]
        #del self.__nim
        self.__vtkimport.CopyImportVoidPointer(self.__data_string,len(self.__data_string))
        #self.__vtkimport.SetImportVoidPointer(self.__data_string,len(self.__data_string))
        self.__vtkimport.SetDataScalarTypeToFloat()
        self.__vtkimport.SetNumberOfScalarComponents(1)
        #XXX this is all not 100% right...
        #the data in array is z,y,x
        #getVoxDims returns x,y,z

    def GetWidth(self):
        return self.__vtkimport.GetDataExtent()[0]

    def GetHeight(self):
        return self.__vtkimport.GetDataExtent()[1]

    def GetDepth(self):
        return self.__vtkimport.GetDataExtent()[2]

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
            if shared.debug: print "in vtkNifti.SetDataSpacing"
            if shared.debug: print "negative number of dimensions not supported! ;-)"
        else:
            self.__spacing=args[:3]
        if shared.debug: print args,self.__spacing
        self.__vtkimport.SetDataSpacing(self.__spacing)

    def GetDataSpacing(self):
        if shared.debug: print self.__spacing, "*******************"
        return self.__spacing
         
    def GetOutput(self):
        return self.__vtkimport.GetOutput()

    def GetFilename(self):
        if shared.debug: print self.__filename
        return self.__filename

    def GetDataExtent(self):
        return self.__vtkimport.GetDataExtent()

    def GetQForm(self):
        return self.__nim.get_affine()

    @property
    def nifti_voxdim(self):
        return self.__nim.get_header()['pixdim'][:3]

    @property
    def shape(self):
        return self.__nim.shape
