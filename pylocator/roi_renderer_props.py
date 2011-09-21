from __future__ import division
import sys, os
import vtk

import gobject
import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu
from matplotlib.cbook import Bunch

from events import EventHandler, UndoRegistry, Viewer
from markers import Marker
from shared import shared

from color_seq import colord, colorSeq

from surf_params import SurfParams

from decimate_filter import DecimateFilter
from connect_filter import ConnectFilter
from vtkNifti import vtkNiftiImageReader

class RoiParams(SurfParams):
    intensity = 0.5

    def set_lighting(self):
        surf_prop = self.isoActor.GetProperty()
        surf_prop.SetAmbient(.2)
        surf_prop.SetDiffuse(.3)
        surf_prop.SetSpecular(.5)

class RoiRendererProps(gtk.Window, Viewer):
    """
    CLASS: RoiRendererProps
    DESCR: 
    """

    SCROLLBARSIZE = 150,20
    lastColor = SurfParams.color
    paramd = {}   # a dict from names to SurfParam instances

    def __init__(self, sr): #, pwxyz):
        """sr is a SurfRenderer"""
        gtk.Window.__init__(self)
        self.set_default_size(300,400)
        self.set_title('ROI rendering')

        self.sr = sr
        self.interactorStyle = self.sr.GetInteractorStyle()


        self.sr.AddObserver('KeyPressEvent', self.key_press)
        
        self.notebook = gtk.Notebook()
        self.notebook.show()

        vbox = gtk.VBox()
        vbox.show()
        vbox.pack_start(self.notebook, True, True)
        self.add(vbox)

        self._make_intensity_frame()
        #self._make_camera_control()
        self._make_seqment_props_frame()
        self._make_pipeline_frame()
        #self._make_picker_frame()


        def hide(*args):
            self.hide()
            return True
        self.connect('delete_event', hide)

        # action area
        hbox = gtk.HBox()
        hbox.show()
        vbox.pack_start(hbox, False, False)        


        button = gtk.Button(stock=gtk.STOCK_CANCEL)
        button.show()
        button.connect('clicked', hide)
        hbox.pack_start(button, True, True)        

            
        button = ButtonAltLabel('Render', gtk.STOCK_EXECUTE)
        button.show()
        button.connect('clicked', self.render)
        hbox.pack_start(button, True, True)        

        button = gtk.Button(stock=gtk.STOCK_OK)
        button.show()
        button.connect('clicked', hide)
        hbox.pack_start(button, True, True)        


    def key_press(self, interactor, event):
        key = interactor.GetKeySym()
        #XXX this is annoying in dwm (and probably elsewhere)
        #if self.pickerName is None:
            #error_msg('You must select the pick segment in the Picker tab')
            #return
        def checkPickerName():
            if self.pickerName is None:
                error_msg('You must select the pick segment in the Picker tab')
                return False
            return True

        if key.lower()=='q': #hehehe
            gtk.main_quit()
        if key.lower()=='i':
            if not checkPickerName():
                return
            print "Inserting Marker"
            x,y = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.PickFromListOn()
            o = self.paramd[self.pickerName]
            picker.AddPickList(o.isoActor)
            picker.SetTolerance(0.005)
            picker.Pick(x, y, 0, self.sr.renderer)
            points = picker.GetPickedPositions()
            numPoints = points.GetNumberOfPoints()
            if numPoints<1: return
            pnt = points.GetPoint(0)

            marker = Marker(xyz=pnt,
                            rgb=EventHandler().get_default_color(),
                            radius=shared.ratio*3)

            EventHandler().add_marker(marker)
        elif key.lower()=='x':
            if not checkPickerName():
                return
            x,y = interactor.GetEventPosition()
            picker = vtk.vtkCellPicker()
            picker.PickFromListOn()
            for o in self.paramd.values():
                picker.AddPickList(o.isoActor)
            picker.SetTolerance(0.01)
            picker.Pick(x, y, 0, self.sr.renderer)
            cellId = picker.GetCellId()
            if cellId==-1:
                pass
            else:
                o = self.paramd.values()[0]
                o.remove.RemoveCell(cellId)
                interactor.Render()
        elif key.lower()=='e':
            if not checkPickerName():
                return
            o = self.paramd.values()[0]
            pw = o.planeWidget
            if pw.GetEnabled():
                pw.EnabledOff()
            else:
                pw.EnabledOn()


        
    def render(self, *args):
        self.sr.Render()
            
    def _make_pipeline_frame(self):
        """
        Set up the surface rendering pipeline

        This class will provide an attibutes dictionary that the
        SufaceRenderer class can use
        """


        vbox = gtk.VBox()
        vbox.show()
        vbox.set_spacing(3)
        
        label = gtk.Label('Pipeline')
        label.show()
        self.notebook.append_page(vbox, label)
        self.vboxPipelineFrame = vbox

        self.update_pipeline_frame()
        
        
    def update_pipeline_frame(self):

        vbox = self.vboxPipelineFrame

        decattrs = DecimateFilter.labels.keys()
        decattrs.sort()

        
        widgets = vbox.get_children()
        for w in widgets:
            vbox.remove(w)

        names = self.paramd.keys()
        names.sort()



        if not len(names):
            label = gtk.Label('No segments defined')
            label.show()
            vbox.pack_start(label)
            return        

        
        frame = gtk.Frame('Segments')
        frame.show()
        frame.set_border_width(5)
        vbox.pack_start(frame, True, True)

        boxRadio = gtk.VBox()
        boxRadio.show()
        frame.add(boxRadio)



        def get_active_name():
            for name, button in buttonNames.items():
                if button.get_active():
                    return name



        def update_params(*args):

            name = get_active_name()

            # set the active props of the filter frames
            self.buttonUseConnect.set_active(self.paramd[name].useConnect)
            self.buttonUseDecimate.set_active(self.paramd[name].useDecimate)

            activeButton = connectExtractButtons[self.paramd[name].connect.mode]
            activeButton.set_active(True)

            # fill in the decimate entry boxes
            for attr in decattrs:
                s = DecimateFilter.labels[attr]
                fmt = DecimateFilter.fmts[attr]
                entry = self.__dict__['entry_' + attr]
                val = getattr(self.paramd[name].deci, attr)
                entry.set_text(fmt%val)


        # set the active segment by name
        lastButton = None
        buttonNames = {}
        for name in names:
            button = gtk.RadioButton(lastButton)
            button.set_label(name)
            button.set_active(name==names[0])
            button.show()
            button.connect('clicked', update_params)
            boxRadio.pack_start(button, True, True)
            buttonNames[name] = button
            lastButton = button


        segmentName = get_active_name()
        framePipelineFilters = gtk.Frame('Pipeline filters')
        framePipelineFilters.show()
        framePipelineFilters.set_border_width(5)
        vbox.pack_start(framePipelineFilters, True, True)

        frameConnectFilter = gtk.Frame('Connect filter settings')
        frameConnectFilter.show()
        frameConnectFilter.set_border_width(5)
        frameConnectFilter.set_sensitive(self.paramd[segmentName].useConnect)
        vbox.pack_start(frameConnectFilter, True, True)

        frameDecimateFilter = gtk.Frame('Decimate filter settings')
        frameDecimateFilter.show()
        frameDecimateFilter.set_border_width(5)
        frameDecimateFilter.set_sensitive(self.paramd[segmentName].useDecimate)
        vbox.pack_start(frameDecimateFilter, True, True)

        
        def connect_toggled(button):
            frameConnectFilter.set_sensitive(button.get_active())
            name = get_active_name()
            self.paramd[name].useConnect  = button.get_active()
            self.paramd[name].update_pipeline()


        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        framePipelineFilters.add(vboxFrame)

        self.buttonUseConnect = gtk.CheckButton('Use connect filter')
        self.buttonUseConnect.show()
        self.buttonUseConnect.set_active(self.paramd[segmentName].useConnect)
        self.buttonUseConnect.connect('toggled', connect_toggled)
        vboxFrame.pack_start(self.buttonUseConnect, True, True)

        def decimate_toggled(button):
            frameDecimateFilter.set_sensitive(button.get_active())
            name = get_active_name()
            self.paramd[name].useDecimate = button.get_active()
            self.paramd[name].update_pipeline()

        self.buttonUseDecimate = gtk.CheckButton('Use decimate filter')
        self.buttonUseDecimate.show()
        self.buttonUseDecimate.set_active(self.paramd[segmentName].useDecimate)
        self.buttonUseDecimate.connect('toggled', decimate_toggled)
        vboxFrame.pack_start(self.buttonUseDecimate, True, True)


        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frameConnectFilter.add(vboxFrame)


        extractModes = ConnectFilter.num2mode.items()
        extractModes.sort()



        def set_extract_mode(button, num):
            name = get_active_name()
            self.paramd[name].connect.mode = num

        lastButton = None
        connectExtractButtons = {}
        for num, name in extractModes:
            button = gtk.RadioButton(lastButton)
            button.set_label(name)
            button.show()
            button.connect('toggled', set_extract_mode, num)
            vboxFrame.pack_start(button, True, True)
            connectExtractButtons[num] = button
            lastButton = button
        activeButton = connectExtractButtons[self.paramd[segmentName].connect.mode]
        activeButton.set_active(True)

        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frameDecimateFilter.add(vboxFrame)


        table = gtk.Table(len(decattrs),2)
        table.set_col_spacings(3)
        table.set_row_spacings(3)
        table.show()
        vboxFrame.pack_start(table, True, True)        

        def make_row(name, default, fmt='%1.1f'):
            label = gtk.Label(name)
            label.show()
            label.set_alignment(xalign=1, yalign=0.5)
            entry = gtk.Entry()
            entry.show()
            entry.set_text(fmt%default)
            entry.set_width_chars(10)
            table.attach(label, 0, 1, make_row.rownum, make_row.rownum+1,
                         xoptions=gtk.FILL, yoptions=0)
            table.attach(entry, 1, 2, make_row.rownum, make_row.rownum+1,
                         xoptions=gtk.EXPAND|gtk.FILL, yoptions=0)
            make_row.rownum += 1
            return label, entry
        make_row.rownum=0

        for attr in decattrs:
            label = DecimateFilter.labels[attr]
            fmt = DecimateFilter.fmts[attr]

            val = getattr(self.paramd[segmentName].deci, attr)
            label, entry = make_row(label, val, fmt)
            self.__dict__['label_' + attr] = label
            self.__dict__['entry_' + attr] = entry



        def apply(button):
            name = get_active_name()
            if self.paramd[name].useDecimate:
                for attr in decattrs:
                    label = self.__dict__['label_' + attr]
                    entry = self.__dict__['entry_' + attr]
                    converter = DecimateFilter.converters[attr]
                    val = converter(entry.get_text(), label, self)
                    if val is None: return
                    setattr(self.paramd[name].deci, attr, val)

            self.paramd[name].update_properties()
            
        button = gtk.Button(stock=gtk.STOCK_APPLY)
        button.show()
        vbox.pack_start(button, True, True)
        button.connect('clicked', apply)
        

    def _make_intensity_frame(self):
        """
        Provides the following attributes
        self.collecting         # intensity collection on
        self.intensitySum = 0   # intensity sum
        self.intensityCnt = 0   # intensity cnt
        self.labelIntensity     # label for intensity entry
        self.entryIntensity     # intensity entry box
        """

        self.collecting = False
        self.intensitySum = 0
        self.intensityCnt = 0


        vbox = gtk.VBox()
        vbox.show()
        vbox.set_spacing(3)
        
        label = gtk.Label('Input')
        label.show()
        self.notebook.append_page(vbox, label)

        frame = gtk.Frame('Select ROI masks')
        frame.show()
        frame.set_border_width(5)
        vbox.pack_start(frame, True, True)
        
        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frame.add(vboxFrame)
        
        #create TreeView
        #Fields: Index, Short filename, long FN, is_active?, opacity
        self.tree_roi = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING,gobject.TYPE_BOOLEAN,gobject.TYPE_FLOAT)
        self.nroi = 0
        self.treev_roi = gtk.TreeView(self.tree_roi)
        self.treev_sel = self.treev_roi.get_selection()
        self.treev_sel.connect("changed",self.treev_sel_changed)
        self.treev_sel.set_mode(gtk.SELECTION_SINGLE)
        renderer = gtk.CellRendererText()
        renderer.set_property("xalign",1.0)
        #renderer.set_xalign(0.0)
        self.col1 = gtk.TreeViewColumn("#",renderer,text=0)
        self.treev_roi.append_column(self.col1)
        self.col2 = gtk.TreeViewColumn("Short filename",renderer,text=1)
        self.treev_roi.append_column(self.col2)
        self.treev_roi.show()
        vboxFrame.pack_start(self.treev_roi,True,True)
        #Buttons for TreeView
        hbox = gtk.HBox()
        vboxFrame.pack_start(hbox,False,False)
        button1 = gtk.Button(stock=gtk.STOCK_ADD)
        button1.connect("clicked",self.add_roi)
        hbox.pack_start(button1)
        button2 = gtk.Button(stock=gtk.STOCK_REMOVE)
        button2.connect("clicked",self.rm_roi)
        hbox.pack_start(button2)
        hbox.show_all()

        #Edit properties of one ROI
        self.props_frame = gtk.Frame('Properties')
        self.props_frame.set_border_width(5)
        vboxFrame.pack_start(self.props_frame,False,False)
        vboxProps = gtk.VBox()
        self.props_frame.add(vboxProps)
        vboxProps.pack_start(gtk.Label("Opacity"))
        self.scrollbar_opacity = gtk.HScrollbar()
        self.scrollbar_opacity.show()
        self.scrollbar_opacity.set_size_request(*self.SCROLLBARSIZE)
        self.scrollbar_opacity.set_range(0, 1)
        self.scrollbar_opacity.set_increments(.05, .2)
        self.scrollbar_opacity.set_value(1.0)
        self.scrollbar_opacity.connect('value_changed', self.change_opacity_of_roi)
        vboxProps.pack_start(self.scrollbar_opacity)
        tmp = gtk.HBox()
        vboxProps.pack_start(tmp)
        tmp.pack_start(gtk.Label("Color"),False,False)
        self.color_chooser = ColorChooser()
        self.color_chooser.connect("color_changed",self.change_color_of_roi)
        tmp.pack_start(self.color_chooser,True,False)


        #vboxProps.pack_start()
        vboxProps.show_all()


    def add_roi(self,*args):
        dialog = gtk.FileSelection('Choose filename for ROI mask')
        dialog.set_filename(shared.get_last_dir())
        dialog.show()
        response = dialog.run()
        if response==gtk.RESPONSE_OK:
            fname = dialog.get_filename()
            dialog.destroy()
            try: 
                #Actually add ROI 
                self.nroi+=1
                tree_iter = self.tree_roi.append(None)
                self.tree_roi.set(tree_iter,0,self.nroi,1,os.path.split(fname)[1],2,fname,3,True)

                roi_image_reader = vtkNiftiImageReader()
                roi_image_reader.SetFileName(fname)
                roi_image_reader.Update()
                roi_id = self.tree_roi.get(tree_iter,0) 
                if not self.paramd.has_key(roi_id):
                    self.paramd[roi_id] = RoiParams(self.sr.renderer, self.sr.interactor)
                    self.paramd[roi_id].set_image_data(roi_image_reader.GetOutput())
                    self.paramd[roi_id].update_pipeline()
                    print self.paramd[roi_id].intensity
                    self.sr.Render()
            except IOError:
                error_msg(
                    'Could not load ROI mask from %s' % fname, 
                    )
            
            else:
                shared.set_file_selection(fname)
        else: dialog.destroy()

    def rm_roi(self,*args):
        treestore,treeiter = self.treev_sel.get_selected()
        roi_id = treestore.get(treeiter,0)
        treestore.remove(treeiter)
        self.paramd[roi_id].destroy()
        del self.paramd[roi_id]

    def treev_sel_changed(self,selection):
        treeiter = selection.get_selected()[1]
        if treeiter:
            self.props_frame.show_all()
            #print "selection changed", self.tree_roi.get(treeiter,0,1,2)
            roi_id = self.tree_roi.get(treeiter,0)
            try:
                self.color_chooser.color = gtk.gdk.Color(*(self.paramd[roi_id].color))
            except Exception, e:
                print "During setting color of color chooser:", type(e),e
            try:
                self.scrollbar_opacity.set_value(self.paramd[roi_id].opacity)
            except Exception, e:
                print "During setting value of opacity scrollbar:", type(e),e
        else:
            self.props_frame.hide()

    def change_color_of_roi(self,*args):
        treeiter = self.treev_sel.get_selected()[1]
        if treeiter:
            roi_id = self.tree_roi.get(treeiter,0)
            self.paramd[roi_id].set_color(self.color_chooser.color)

    def change_opacity_of_roi(self,*args):
        treeiter = self.treev_sel.get_selected()[1]
        if treeiter:
            roi_id = self.tree_roi.get(treeiter,0)
            self.paramd[roi_id].set_opacity(self.scrollbar_opacity.get_value())

        

    def _make_seqment_props_frame(self):
        """
        Control the sement attributes (delete, opacity, etc)
        """


        vbox = gtk.VBox()
        vbox.show()
        vbox.set_spacing(3)
        
        label = gtk.Label('Segments')
        label.show()
        self.notebook.append_page(vbox, label)

        frame = gtk.Frame('Segment properties')
        frame.show()
        frame.set_border_width(5)
        vbox.pack_start(frame, True, True)

        
        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frame.add(vboxFrame)

        self.vboxSegPropsFrame = vboxFrame
        self.update_segments_frame() 

        
    def update_segments_frame(self):
        'Update the segment props with the latest segments'

        vbox = self.vboxSegPropsFrame
        
        widgets = vbox.get_children()
        for w in widgets:
            vbox.remove(w)

        names = self.paramd.keys()

        if not len(names):
            label = gtk.Label('No segments')
            label.show()
            vbox.pack_start(label)
            return
        
        names.sort()
        numrows = len(names)+1
        numcols = 2

        table = gtk.Table(numrows,numcols)
        table.set_col_spacings(3)
        table.show()
        vbox.pack_start(table, True, True)        

        delete = gtk.Label('Hide')
        delete.show()
        opacity = gtk.Label('Opacity')
        opacity.show()
        

        table.attach(delete, 0, 1, 0, 1, xoptions=gtk.FILL, yoptions=0)
        table.attach(opacity, 1, 2, 0, 1, xoptions=gtk.EXPAND|gtk.FILL, yoptions=0)
        deleteButtons = {}
        opacityBars = {}


        class OpacityCallback:
            def __init__(self, sr, name, paramd):
                """
                sr is the surf renderer instance
                name is the name of the surface
                paramd is the dict mapping names to objects

                You don't want to pass the object itself because it is
                bound at init time but you to be able to dynamically
                update
                """
                self.name = name
                self.sr = sr
                self.paramd = paramd

            def __call__(self, bar):
                val = bar.get_value()
                self.paramd[self.name].isoActor.GetProperty().SetOpacity(val)
                self.sr.Render()

        class HideCallback:
            def __init__(self, sr, name, paramd):
                """
                sr is the surf renderer instance
                name is the name of the surface
                paramd is the dict mapping names to objects

                You don't want to pass the object itself because it is
                bound at init time but you to be able to dynamically
                update                
                """
                self.sr = sr
                self.name = name
                self.paramd = paramd
                self.removed = False

            def __call__(self, button):

                if button.get_active():
                    self.paramd[self.name].isoActor.VisibilityOff()
                else:
                    self.paramd[self.name].isoActor.VisibilityOn()
                self.sr.Render()                    

        rownum = 1                
        for name in names:
            hideCallback = HideCallback(self.sr, name, self.paramd)
            opacityCallback = OpacityCallback(self.sr, name, self.paramd)            
            b = gtk.CheckButton(name)
            b.show()
            b.set_active(False)
            b.connect('toggled', hideCallback)
            table.attach(b, 0, 1, rownum, rownum+1,
                         xoptions=False, yoptions=False)
            deleteButtons[name] = b

            scrollbar = gtk.HScrollbar()
            scrollbar.show()
            scrollbar.set_size_request(*self.SCROLLBARSIZE)
            table.attach(scrollbar, 1, 2, rownum, rownum+1,
                         xoptions=True, yoptions=False)
            
            scrollbar.set_range(0, 1)
            scrollbar.set_increments(.05, .2)
            scrollbar.set_value(1.0)


            scrollbar.connect('value_changed', opacityCallback)
            rownum += 1

    def add_segment(self, button):
        'render, man'
        val = self.get_intensity()
        if val is None: return
        name = self.entryName.get_text()
        if not len(name):
            error_msg('You must enter a name in the Intensity tab')
            return

        if not self.paramd.has_key(name):
            self.paramd[name] = SurfParams(self.sr.renderer, self.sr.interactor)

        params = self.paramd[name]
        params.label = name
        params.intensity = val
        params.color = self.lastColor
        params.set_image_data(self.sr.imageData)
        params.update_properties()
        
        self.update_segments_frame() 
        self.update_pipeline_frame()
        self.update_picker_frame()
        
    def interaction_event(self, observer, event):
        if not self.collecting: return 
        xyzv = [0,0,0,0]
        observer.GetCursorData(xyzv)
        self.add_intensity(xyzv[3])
        self.entryIntensity.set_text('%1.1f' % (self.intensitySum/self.intensityCnt))

    def get_intensity(self):
        """
        Get the intensity of value if valid.

        If not warn and return None
        """
        
        val = str2posnum_or_err(self.entryIntensity.get_text(),
                                self.labelIntensity, parent=self)
        return val

            

class OpacityCallback:
    def __init__(self, sr, name, paramd):
        """
        sr is the surf renderer instance
        name is the name of the surface
        paramd is the dict mapping names to objects

        You don't want to pass the object itself because it is
        bound at init time but you to be able to dynamically
        update
        """
        self.name = name
        self.sr = sr
        self.paramd = paramd

    def __call__(self, bar):
        val = bar.get_value()
        self.paramd[self.name].isoActor.GetProperty().SetOpacity(val)

class ColorChooser(gtk.Frame):
    def __init__(self,color=None):
        gtk.Frame.__init__(self)
        self.da = gtk.DrawingArea()
        self.add(self.da)
        self.da.set_size_request(40,20)
        if color==None:
            color=gtk.gdk.Color(1.,1.,1.)
        self.set_color(color)
        self.set_border_width(20)
        self.set_property("shadow-type",gtk.SHADOW_ETCHED_IN)
        self.da.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.da.connect("button-press-event",self.choose_color)

    def set_color(self,color):
        for state in [gtk.STATE_NORMAL,
                      gtk.STATE_ACTIVE,
                      gtk.STATE_PRELIGHT,
                      gtk.STATE_SELECTED,
                      gtk.STATE_INSENSITIVE]:
            self.da.modify_bg(state,color)
        self._color=color
        self.emit("color_changed")

    def get_color(self):
        return self._color

    def choose_color(self, *args):
        dialog = gtk.ColorSelectionDialog('Choose color for ROI')
            
        colorsel = dialog.colorsel

        
        colorsel.set_previous_color(self._color)
        colorsel.set_current_color(self._color)
        colorsel.set_has_palette(True)
    
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            color = colorsel.get_current_color()
            dialog.destroy()
            self.set_color(color)
    
    color = property(get_color,set_color)

gobject.type_register(ColorChooser)
gobject.signal_new("color_changed", 
                   ColorChooser, 
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
