import gtk
import vtk
from render_window import PyLocatorRenderWindow
from events import EventHandler, UndoRegistry
from shared import shared
from dialogs import edit_label_of_marker

INTERACT_CURSOR, MOVE_CURSOR, COLOR_CURSOR, SELECT_CURSOR, DELETE_CURSOR, LABEL_CURSOR, SCREENSHOT_CURSOR = gtk.gdk.ARROW, gtk.gdk.HAND2, gtk.gdk.SPRAYCAN, gtk.gdk.TCROSS, gtk.gdk.X_CURSOR, gtk.gdk.PENCIL, gtk.gdk.ICON

class MarkerWindowInteractor(PyLocatorRenderWindow):
    """
    CLASS: MarkerWindowInteractor
    DESCR: 
    """
    def __init__(self):
        PyLocatorRenderWindow.__init__(self)
        #self.camera = self.renderer.GetActiveCamera()

        
        self.pressFuncs = {1 : self._Iren.LeftButtonPressEvent,
                           2 : self._Iren.MiddleButtonPressEvent,
                           3 : self._Iren.RightButtonPressEvent}
        self.releaseFuncs = {1 : self._Iren.LeftButtonReleaseEvent,
                             2 : self._Iren.MiddleButtonReleaseEvent,
                             3 : self._Iren.RightButtonReleaseEvent}

        self.pressHooks = {}
        self.releaseHooks = {}

        self.vtk_interact_mode = False

    def mouse1_mode_change(self, event):
        """
        Give derived classes toclean up any observers, etc, before
        switching to new mode
        """
        
        pass

    def update_viewer(self, event, *args):
        PyLocatorRenderWindow.update_viewer(self, event, *args)
        if event.find('mouse1')==0:
            self.mouse1_mode_change(event)
        if event=='mouse1 interact':
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_interact()"
            self.set_mouse1_to_interact()
        elif event=='vtk interact':
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_vtkinteract()"
            self.set_mouse1_to_vtkinteract()
        elif event=='mouse1 color':
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_color()"
            self.set_mouse1_to_color()
        elif event=='mouse1 delete':
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_delete()"
            self.set_mouse1_to_delete()
        elif event=='mouse1 label': 
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_label()"
            self.set_mouse1_to_label()
        elif event=='mouse1 select':
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_select()"
            self.set_mouse1_to_select()
        elif event=='mouse1 move':
            if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_move()"
            self.set_mouse1_to_move()

    def get_marker_at_point(self):    
        raise NotImplementedError

    def set_image_data(self, imageData):
        pass
    
    def set_select_mode(self):
        pass

    def set_interact_mode(self):
        if shared.debug: print "set_interact_mode()!!!!"
        self.vtk_interact_mode = False
    
    def set_vtkinteract_mode(self):
        if shared.debug: print "set_vtkinteract_mode()!!!!"

        if (self.vtk_interact_mode == False):
            # mcc XXX: ignore this
            #foo = self.AddObserver('InteractionEvent', self.vtkinteraction_event)
            #print "MarkerWindowInteractor.set_vtkinteract_mode(): AddObserver call returns ", foo
            self.vtk_interact_mode = True
    
    def set_mouse1_to_interact(self):

        if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_interact()"

        self.vtk_interact_mode = False

        # XXX why does this not work
        self.set_interact_mode()

        try: del self.pressHooks[1]
        except KeyError: pass

        try: del self.releaseHooks[1]
        except KeyError: pass

        cursor = gtk.gdk.Cursor (INTERACT_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)

    def vtkinteraction_event(self, *args):
        if shared.debug: print "vtkinteraction_event!!!"
        self.Render()

    def set_mouse1_to_vtkinteract(self):

        if shared.debug: print "MarkerWindowInteractor.set_mouse1_to_vtkinteract()"

        self.set_vtkinteract_mode()

        def button_down(*args):
            #print "button down on brain interact."
            x, y = self.GetEventPosition()
            picker = vtk.vtkPropPicker()
            picker.PickProp(x, y, self.renderer)
            actor = picker.GetActor()
            # now do something with the actor !!!
            #print "actor is ", actor

        def button_up(*args):
            #print "button up on brain interact."
            pass

        self.pressHooks[1] = button_down
        self.releaseHooks[1] = button_up

        cursor = gtk.gdk.Cursor (INTERACT_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)

    def set_mouse1_to_move(self):
        self.set_select_mode()
        cursor = gtk.gdk.Cursor (MOVE_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)

    def set_mouse1_to_delete(self):

        def button_up(*args):
            pass

        def button_down(*args):
            marker = self.get_marker_at_point()
            if marker is None: return
            EventHandler().remove_marker(marker)

        self.pressHooks[1] = button_down
        self.releaseHooks[1] = button_up

        self.set_select_mode()
        cursor = gtk.gdk.Cursor (DELETE_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)

    def set_mouse1_to_select(self):
        
        def button_up(*args):
            pass

        def button_down(*args):
            marker = self.get_marker_at_point()
            if marker is None: return
            isSelected = EventHandler().is_selected(marker)
            if self.interactor.GetControlKey():
                if isSelected: EventHandler().remove_selection(marker)
                else: EventHandler().add_selection(marker)
            else: EventHandler().select_new(marker)

        self.pressHooks[1] = button_down
        self.releaseHooks[1] = button_up

        self.set_select_mode()
        cursor = gtk.gdk.Cursor (SELECT_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)

    def set_mouse1_to_label(self):

        def button_up(*args):
            pass

        def button_down(*args):
            marker = self.get_marker_at_point()
            if marker is None: return
            edit_label_of_marker(marker)
            

        self.pressHooks[1] = button_down
        self.releaseHooks[1] = button_up
        self.set_select_mode()
        cursor = gtk.gdk.Cursor (LABEL_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)
        
    def set_mouse1_to_color(self):

        def button_up(*args):
            pass

        def button_down(*args):
            marker = self.get_marker_at_point()
            if marker is None: return
            color = EventHandler().get_default_color()
            oldColor = marker.get_color()
            UndoRegistry().push_command(
                EventHandler().notify, 'color marker', marker, oldColor)
            EventHandler().notify('color marker', marker, color)

        self.pressHooks[1] = button_down
        self.releaseHooks[1] = button_up
        self.set_select_mode()

        cursor = gtk.gdk.Cursor (COLOR_CURSOR)
        if self.window is not None:
            self.window.set_cursor (cursor)


    def OnButtonDown(self, wid, event):
        """Mouse button pressed."""

        self.lastCamera = self.get_camera_fpu()
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        if shared.debug: print "MarkerWindowInteractor.OnButtonDown(): ctrl=", ctrl,"shift=",shift,"button=",event.button
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)

        if shared.debug: print "MarkerWindowInteractor.OnButtonDown(): pressFuncs=", self.pressFuncs, "pressHooks=", self.pressHooks

        if event.button in self.interactButtons:
            if shared.debug: print "self.vtk_interact_mode =", self.vtk_interact_mode
            if (self.vtk_interact_mode == False):
                self.pressFuncs[event.button]()            

        try: self.pressHooks[event.button]()
        except KeyError: pass

    def OnButtonUp(self, wid, event):
        """Mouse button released."""
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        if shared.debug: print "MarkerWindowInteractor.OnButtonUp(): ctrl=", ctrl,"shift=",shift, "button=",event.button
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)


        if event.button in self.interactButtons:
            if shared.debug: print "self.vtk_interact_mode =", self.vtk_interact_mode
            if (self.vtk_interact_mode == False):
                self.releaseFuncs[event.button]()            

        try: self.releaseHooks[event.button]()
        except KeyError: pass

        thisCamera = self.get_camera_fpu()
        try: self.lastCamera
        except AttributeError: pass  # this
        else:
            if thisCamera != self.lastCamera:
                UndoRegistry().push_command(self.set_camera, self.lastCamera)

        return True

    def get_plane_points(self, pw):
        return pw.GetOrigin(), pw.GetPoint1(), pw.GetPoint2()

    def set_plane_points(self, pw, pnts):
        o, p1, p2 = pnts
        pw.SetOrigin(o)
        pw.SetPoint1(p1)
        pw.SetPoint2(p2)
        pw.UpdatePlacement()

