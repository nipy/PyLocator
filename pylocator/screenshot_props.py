import gtk
from gtkutils import error_msg
from resources import camera_small_fn
from shared import shared

INTERACT_CURSOR, MOVE_CURSOR, COLOR_CURSOR, SELECT_CURSOR, DELETE_CURSOR, LABEL_CURSOR, SCREENSHOT_CURSOR = gtk.gdk.ARROW, gtk.gdk.HAND2, gtk.gdk.SPRAYCAN, gtk.gdk.TCROSS, gtk.gdk.X_CURSOR, gtk.gdk.PENCIL, gtk.gdk.ICON

class ScreenshotProps(gtk.VBox):
    """
    CLASS: ScreenshotProps
    DESC: 
    """

    def __init__(self):
        self._sts = [] # Stores all PyLocatorRenderWindows to invoke on button press
        gtk.VBox.__init__(self)

        self.scrolled_window = gtk.ScrolledWindow()
        self.inner_vbox = gtk.VBox()
        self.inner_vbox.set_spacing(20)
        self.scrolled_window.add_with_viewport(self.inner_vbox)
        self.pack_start(self.scrolled_window)
        self.scrolled_window.show_all()

        self.__make_filename_frame()
        self.__make_magnification_frame()
        self.__make_buttons_frame()
        self.__make_explanation_frame()

        self.show()


    def __make_filename_frame(self):
        frame = gtk.Frame('Filename pattern ')
        frame.set_border_width(5)
        frame.show()

        vbox = gtk.VBox()
        frame.add(vbox)
        vbox.show()

        self.entryFn = gtk.Entry()
        self.entryFn.show()
        self.entryFn.set_text('pylocator%03i.png')
        vbox.pack_start(self.entryFn,False,False)

        self.buttonPropose = gtk.Button(label="Propose!")
        self.buttonPropose.show()
        self.buttonPropose.connect('clicked', self.propose_fn)
        vbox.pack_start(self.buttonPropose, True, False)

        self.inner_vbox.pack_start(frame,False,False)

    def __make_magnification_frame(self):
        frame = gtk.Frame('Magnification')
        frame.set_border_width(5)
        frame.show()
        adjustment = gtk.Adjustment(2, 1, 10, 1, 1, 0)
        self.sbMag = gtk.SpinButton(adjustment)
        self.sbMag.show()
        frame.add(self.sbMag)
        self.inner_vbox.pack_start(frame,False,False)

    def __make_explanation_frame(self):
        frame = gtk.Frame('Hints')
        frame.set_border_width(10)
        frame.show()
        
        hbox = gtk.HBox()
        hbox.show()
        frame.add(hbox)

        self.explain = gtk.Label()
        self.explain.set_line_wrap(True)
        self.explain.set_markup(
        """
<small>
Set a filename pattern to use for screenshots. Needs a "%03i" for automatic numbering.

Use the buttons above to take a screenshot of one of the 3d-widgets. Alternatively, take screenshots of all widgets using the button below.

Set the magnification factor to increase image size for screenshots.
</small>
""")
        self.explain.set_size_request(200,-1)
        self.explain.show()
        hbox.pack_start(self.explain, False, False, 10)
        
        self.inner_vbox.pack_start(frame,False,False)

    def __make_buttons_frame(self):
        #Frame for buttons for screenshots
        frame = gtk.Frame('Take screenshot of')
        frame.set_border_width(5)
        frame.show()

        self.buttons_vbox = gtk.VBox()
        frame.add(self.buttons_vbox)

        self.inner_vbox.pack_start(frame,False,False,padding=10)

    def create_buttons(self):
        def make_button(pixbuf):
            camera = gtk.Image()
            camera.set_from_pixbuf(pixbuf)
            camera.show()
            button = gtk.Button(label=None)
            button.set_image(camera)
            return button

        def insert_row(txt, pixbuf, row):
            label = gtk.Label(txt)
            label.show()
            hbox=gtk.HBox()
            hbox.show()
            hbox.pack_end(label,False,False)
            button = make_button(pixbuf)
            button.show()
            table.attach(hbox,0,1,row,row+1,xoptions=gtk.FILL,yoptions=0)
            table.attach(button,1,2,row,row+1,xoptions=gtk.FILL,yoptions=0)
            return label, button

        table = gtk.Table(len(self._sts)+1,2)
        table.set_col_spacings(10)
        table.set_row_spacings(3)
        table.show()
        self.buttons_vbox.pack_start(table,padding=10)

        cameraPixBuf = gtk.gdk.pixbuf_new_from_file(camera_small_fn)
        #  button for all screenshots
        label, button = insert_row("All views",cameraPixBuf,0)
        button.connect('clicked', self.take_all_shots)

        for i,st in enumerate(self._sts):
            label, button = insert_row(
                                st.screenshot_button_label,
                                cameraPixBuf, i+1 
                            )
            button.connect('clicked',self.take_shot,i)

        self.buttons_vbox.show()

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
            
    def append_screenshot_taker(self,st):
        self._sts.append(st)

    def take_shot(self, button, idx):
        """For one PyLocatorRenderWindow, take a SS"""
        #print "take_shot", args
        if len(self._sts)==0:
            error_msg("Cannot take screenshots: \nNo instances registered.")
            return False
        fn_pattern = self.entryFn.get_text()
        mag = self.sbMag.get_value()
        self._sts[idx].take_screenshot(fn_pattern, mag)

    def take_all_shots(self, *args):
        """For each PyLocatorRenderWindow in list, take a SS"""
        if len(self._sts)==0:
            error_msg("Cannot take screenshots: \nNo instances registered.")
            return False
        fn_pattern = self.entryFn.get_text()
        mag = self.sbMag.get_value()
        for st in self._sts:
            st.take_screenshot(fn_pattern, mag)

