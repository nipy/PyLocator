import vtk
from markers import Marker

import pickle

from scipy import array, zeros
from shared import shared

class Viewer:
    def update_viewer(self, event, *args):
        raise NotImplementedError


class UndoRegistry:
    __sharedState = {}
    commands = []
    lastPop = None, []

    def __init__(self):
        self.__dict__ = self.__sharedState    

    def push_command(self, func, *args):
        self.commands.append((func, args))

    def undo(self):
        if len(self.commands)==0: return
        func, args = self.commands.pop()
        self.lastPop = func, args
        func(*args)

        
    def flush(self):
        self.commands = []

    def get_last_pop(self):
        return self.lastPop

class EventHandler:
    __sharedState = {}
    markers = vtk.vtkActorCollection()
    defaultColor = (0,0,1)
    labelsOn = 1
    observers = {}
    selected = {}
    __NiftiQForm=None
    __NiftiSpacings=(1.0,1.0,1.0)
    __NiftiShape=None

    def __init__(self):
        self.__dict__ = self.__sharedState            

    def add_selection(self, marker):
        self.selected[marker] = 1
        self.notify('select marker', marker)
        
    def remove_selection(self, marker):
        if self.selected.has_key(marker):
            del self.selected[marker]
            self.notify('unselect marker', marker)
        
    def clear_selection(self):
        for oldMarker in self.selected.keys():
            self.remove_selection(oldMarker)

    def select_new(self, marker):
        self.clear_selection()
        self.add_selection(marker)
    
    def add_marker(self, marker):
        # break undo cycle 
        func, args = UndoRegistry().get_last_pop()
        #if shared.debug: print 'add', func, args
        if len(args)==0 or \
               (func, args[0]) != (self.add_marker, marker):
            UndoRegistry().push_command(self.remove_marker, marker)
        self.markers.AddItem(marker)
        self.notify('add marker', marker)


    def remove_marker(self, marker):
        # break undo cycle

        func, args = UndoRegistry().get_last_pop()
        #if shared.debug: print 'remove', func, args
        if len(args)==0 or \
               (func, args[0]) != (self.remove_marker, marker):
            UndoRegistry().push_command(self.add_marker, marker)
        self.markers.RemoveItem(marker)
        self.notify('remove marker', marker)

    def get_markers(self):
        return self.markers

    def get_markers_as_seq(self):
        numMarkers = self.markers.GetNumberOfItems()
        self.markers.InitTraversal()
        return [self.markers.GetNextActor() for i in range(numMarkers)]


    def set_default_color(self, color):
        self.defaultColor = color

    def get_default_color(self):
        return self.defaultColor


    def save_markers_as(self, fname):
        self.markers.InitTraversal()
        numMarkers = self.markers.GetNumberOfItems()
        lines = []; conv_lines = []

        for i in range(numMarkers):
            marker = self.markers.GetNextActor()
            if marker is None: continue
            else:
                #XXX if self.__Nifti:
                #if self.__NiftiQForm is not None:
                #    conv_marker=marker.convert_coordinates(self.__NiftiQForm,self.__NiftiSpacings,self.__NiftiShape)
                #    #XXX conv_marker=marker.convert_coordinates(QForm)
                #    conv_lines.append(conv_marker.to_string())

                lines.append(marker.to_string())
        lines.sort()

        fh = file(fname, 'w')
        fh.write('\n'.join(lines) + '\n')
        #if self.__NiftiQForm is not None:
        #    fn = file(fname+".conv", 'w') #only needed for nifti, but what the hell
        #    conv_lines.sort()
        #    fn.write('\n'.join(conv_lines) + '\n')

    def setNifti(self,QForm,spacings,shape):
        if shared.debug: print "setNifti:", QForm, spacings, shape
        self.__NiftiQForm=QForm
        self.__NiftiSpacings=spacings
        self.__NiftiShape=shape

    def set_vtkactor(self, vtkactor):
        if shared.debug: print "EventHandler.set_vtkactor()"
        self.vtkactor = vtkactor

    def save_registration_as(self, fname):
        if shared.debug: print "EventHandler.save_registration_as(", fname,")"
        fh = file(fname, 'w')

        # XXX mcc: somehow get the transform for the VTK actor. aiieeee
        #xform = self.vtkactor.GetUserTransform()
        loc = self.vtkactor.GetOrigin()
        pos = self.vtkactor.GetPosition()
        scale = self.vtkactor.GetScale()
        mat = self.vtkactor.GetMatrix()
        orient = self.vtkactor.GetOrientation()
        
        if shared.debug: print "EventHandler.save_registration_as(): vtkactor has origin, pos, scale, mat, orient=", loc, pos, scale, mat, orient, "!!"


        def vtkmatrix4x4_to_array(vtkmat):
            scipy_array = zeros((4,4), 'd')

            for i in range(0,4):
                for j in range(0,4):
                    scipy_array[i][j] = mat.GetElement(i,j)

            return scipy_array

        scipy_mat = vtkmatrix4x4_to_array(mat)

        pickle.dump(scipy_mat, fh)
        fh.close()
        
        
    def load_markers_from(self, fname):

        self.notify('render off')
        for line in file(fname, 'r'):
            marker = Marker.from_string(line)
            self.add_marker(marker)
        self.notify('render on')
        UndoRegistry().flush()

    def attach(self, observer):
        self.observers[observer] = 1

    def detach(self, observer):
        try:
            del self.observers[observer]
        except KeyError: pass

    def notify(self, event, *args):
        for observer in self.observers.keys():
            if shared.debug: print "EventHandler.notify(", event, "): calling update_viewer for ", observer
            observer.update_viewer(event, *args)

    def get_labels_on(self):
        return self.labelsOn

    def set_labels_on(self):
        self.labelsOn = 1
        self.notify('labels on')

    def set_labels_off(self):
        self.labelsOn = 0
        self.notify('labels off')


    def is_selected(self, marker):
        return self.selected.has_key(marker)

    def get_selected(self):
        return self.selected.keys()

    def get_num_selected(self):
        return len(self.selected)
