from gtk import gdk
import gtk
import vtk
from GtkGLExtVTKRenderWindowInteractor import GtkGLExtVTKRenderWindowInteractor
from events import EventHandler, UndoRegistry, Viewer
from gtkutils import error_msg
import re

from shared import shared


INTERACT_CURSOR, MOVE_CURSOR, COLOR_CURSOR, SELECT_CURSOR, DELETE_CURSOR, LABEL_CURSOR, SCREENSHOT_CURSOR = gtk.gdk.ARROW, gtk.gdk.HAND2, gtk.gdk.SPRAYCAN, gtk.gdk.TCROSS, gtk.gdk.X_CURSOR, gtk.gdk.PENCIL, gtk.gdk.ICON

class ScreenshotTaker(GtkGLExtVTKRenderWindowInteractor):
    """
    CLASS: ScreenshotTaker
    DESCR: 
    """
    def __init__(self,*args):
        GtkGLExtVTKRenderWindowInteractor.__init__(self,*args)
        self.spd = None

    #def OnKeyPress(self, wid, event=None):
    #    if (event.keyval == gdk.keyval_from_name("s") or
    #        event.keyval == gdk.keyval_from_name("S")):
    #        print "KeyPress Screenshot"
    #        self.take_screenshot()
    #        return True

    def take_screenshot(self):
        #print "Start Screenshot"
        if not self.spd:
            error_msg("Cannot take screenshot: Properties not set.")
            return False

        fn = self.spd.entryFn.get_text()%shared.screenshot_cnt
        mag = int(round(self.spd.sbMag.get_value()))

        shared.screenshot_cnt+=1

        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(self.renWin)
        w2if.SetMagnification(mag) #shared.screenshot_magnification)
        w2if.Update()
         
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(fn)
        writer.SetInput(w2if.GetOutput())
        writer.Write()
        #print "Ende Screenshot"
        self.Render()
        return

    def set_mouse1_to_screenshot(self):
        self.set_select_mode()
        cursor = gtk.gdk.Cursor (SCREENSHOT_CURSOR)
        self.pressHooks[1] = self.take_screenshot
        if self.window is not None:
            self.window.set_cursor (cursor)

    def set_screenshot_props(self, spd, label):
        self.spd = spd
        spd.append_screenshot_taker(self,label)

class ScreenshotProps(gtk.Window, Viewer):
    """
    CLASS: ScreenshotProps
    DESC: 
    """

    #SCROLLBARSIZE = 150,20
    def __init__(self):
        """Init"""
        self._sts = [] # Stores all ScreenshotTakers to invoke on button press
        gtk.Window.__init__(self)
        self.set_default_size(400,200)
        self.set_title('Screenshot settings')
        
        self.vbox = gtk.VBox()
        self.add(self.vbox)

        self.vbox1 = gtk.VBox()
        self.frameFn = gtk.Frame('Filename pattern ')
        self.frameFn.set_border_width(5)
        self.frameFn.show()
        self.entryFn = gtk.Entry()
        self.entryFn.show()
        self.entryFn.set_text('pylocator%03i.png')
        self.buttonPropose = gtk.Button(label="Propose!")
        self.buttonPropose.show()
        self.buttonPropose.connect('clicked', self.propose_fn)
        
        self.vbox1.pack_start(self.entryFn, True, False)
        self.vbox1.pack_start(self.buttonPropose, True, False)

        self.frameFn.add(self.vbox1)

        self.vbox.pack_start(self.frameFn,True,False)

        #Spinbox for magnification
        self.frameMag = gtk.Frame('Magnification')
        self.frameMag.set_border_width(5)
        self.frameMag.show()
        adjustment = gtk.Adjustment(2, 1, 10, 1, 1, 0)
        self.sbMag = gtk.SpinButton(adjustment)
        self.sbMag.show()
        self.frameMag.add(self.sbMag)
        self.vbox.pack_start(self.frameMag,True,False)

        def hide(*args):
            self.hide()
            return True

        self.connect('delete_event', hide)

        #self.sep = gtk.VSeparator()
        #self.vbox.pack_start(self.sep,True,True)

        self.vbox2 = gtk.VBox()
        self.vbox.pack_start(self.vbox2,True,False)
        
        self.explain = gtk.Label()
        self.explain.set_line_wrap(True)
        self.explain.set_markup(
        """
<i>Hints:</i>
  <small>
  - Set a filename pattern to use for screenshots. Needs a "%03i" for automatic numbering.
  - Use the buttons above to take a screenshot of one of the 3d-widgets. Alternatively, take screenshots of all widgets using the button below.
  - Set the magnification factor to increase image size for screenshots
  </small>
""")
        self.explain.show()

        #Frame for buttons for screenshots
        self.frameBut = gtk.Frame('Take screenshot')
        self.frameBut.set_border_width(5)
        self.frameBut.show()
        self.vbox_buttons = gtk.VBox()
        self.vbox_buttons.show()
        self.frameBut.add(self.vbox_buttons)
        #Button for SS from all renderers
        self.buttonPic = gtk.Button(label="Take all screenshots")
        self.buttonPic.show()
        self.buttonPic.connect('clicked', self.take_all_shots)
        self.vbox_buttons.pack_end(self.buttonPic, True, False)        
        self.vbox2.pack_start(self.frameBut,True,False)

        self.buttonOK = gtk.Button(stock=gtk.STOCK_OK)
        self.buttonOK.show()
        self.buttonOK.connect('clicked', hide)

        self.vbox2.pack_end(self.buttonOK, True, False)        
        self.vbox2.pack_end(self.explain, True, False)        

        self.vbox1.show()
        self.vbox2.show()
        self.vbox.show()

    def propose_fn(self,*args):
        mri_fn = shared.lastSel
        if len(mri_fn) == 0:
            error_msg("Cannot propose filename: \nFilename of MRI unknown")
            return False
        for suff in [".nii.gz",".nii"]:
            if mri_fn.endswith(suff):
                mri_fn = mri_fn[:-len(suff)]
        self.entryFn.set_text(mri_fn+"_pylocator%03i.png")
        return True
            
    def append_screenshot_taker(self,st,label):
        self._sts.append(st)
        bt = gtk.Button(label=label)
        bt.connect('clicked',self.take_shot,len(self._sts)-1)
        bt.show()
        self.vbox_buttons.pack_start(bt)

    def take_shot(self, button, idx):
        """For one ScreenshotTaker, take a SS"""
        #print "take_shot", args
        if len(self._sts)==0:
            error_msg("Cannot take screenshots: \nNo instances registered.")
            return False
        self._sts[idx].take_screenshot()

    def take_all_shots(self, *args):
        """For each ScreenshotTaker in list, take a SS"""
        if len(self._sts)==0:
            error_msg("Cannot take screenshots: \nNo instances registered.")
            return False
        for st in self._sts:
            st.take_screenshot()

