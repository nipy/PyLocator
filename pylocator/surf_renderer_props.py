from __future__ import division
import sys, os
import vtk

import gobject
import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu

from events import EventHandler, UndoRegistry
from markers import Marker
from shared import shared

from colors import ColorChooser, colord, colorSeq

from list_toolbar import ListToolbar
from surf_params import SurfParams

from decimate_filter import DecimateFilter
from connect_filter import ConnectFilter

class SurfRendererProps(gtk.VBox):
    """
    CLASS: SurfRendererProps
    DESCR: 
    """

    SCROLLBARSIZE = 150,20
    lastColor = SurfParams.color_
    paramd = {}   # a dict from names to SurfParam instances

    def __init__(self, sr, pwxyz):
        """sr is a SurfRenderer"""

        self.nsurf=0
        self.ignore_pipeline_updates = False

        gtk.VBox.__init__(self)
        self.show()
        self.set_homogeneous(False)

        self.sr = sr
        self.interactorStyle = self.sr.GetInteractorStyle()

        self.sr.AddObserver('KeyPressEvent', self.key_press)
        self.pwxyz = pwxyz
        
        toolbar = self.__create_toolbar()
        self.pack_start(toolbar,False,False)
        toolbar.show()

        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.show()
        self.inner_vbox = gtk.VBox()
        self.inner_vbox.show()
        self.inner_vbox.set_spacing(20)
        self.scrolled_window.add_with_viewport(self.inner_vbox)
        #self.scrolled_window.show()
        #self.inner_vbox.show()
        self.pack_start(self.scrolled_window)

        self._make_segment_list()
        self._make_intensity_frame()
        self._make_picker_frame()

        def hide(*args):
            self.hide()
            return True
        self.connect('delete_event', hide)

        button = ButtonAltLabel('Render', gtk.STOCK_EXECUTE)
        button.show()
        button.connect('clicked', self.render)
        self.pack_start(button, False, False)        

    def __create_toolbar(self):
        conf = [
                [gtk.STOCK_ADD,
                 'Add',
                 'Load ROI from file and render it',
                 self.add_segment
                ],
                [gtk.STOCK_REMOVE, 
                 'Remove', 
                 'Remove selected ROI',
                 self.add_segment
                ],
               ]
        return ListToolbar(conf)

    def _make_segment_list(self):
        #create TreeView
        #Fields: idx, Name 
        self.tree_surf = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        self.nroi = 0
        self.treev_surf = gtk.TreeView(self.tree_surf)
        self.treev_sel = self.treev_surf.get_selection()
        self.treev_sel.connect("changed",self.treev_sel_changed)
        self.treev_sel.set_mode(gtk.SELECTION_SINGLE)
        renderer = gtk.CellRendererText()
        renderer.set_property("xalign",0.0)
        #renderer.set_xalign(0.0)
        self.col1 = gtk.TreeViewColumn("Name",renderer,text=1)
        self.treev_surf.append_column(self.col1)
        #self.treev_roi.show()
        self.inner_vbox.pack_start(self.treev_surf, False)
        #self.treev_surf.show()

        #Empty-indicator
        self.emptyIndicator = gtk.Label('No segment defined')
        self.emptyIndicator.show()
        self.inner_vbox.pack_start(self.emptyIndicator, False)

        #Edit properties of one surface
        self.props_frame = gtk.Frame('Properties')
        self.props_frame.set_border_width(5)
        self.inner_vbox.pack_start(self.props_frame,False,False)
        vboxProps = gtk.VBox()
        self.props_frame.add(vboxProps)
        general_expander = self._make_general_properties_expander()
        vboxProps.pack_start(general_expander, False)
        pipeline_expander = self._make_pipeline_expander()
        vboxProps.pack_start(pipeline_expander, False)

    def _make_general_properties_expander(self):
        expander = gtk.Expander('General settings')
        expander.set_expanded(True)

        vbox = gtk.VBox()
        vbox.show()
        vbox.set_spacing(10)
        expander.add(vbox)

        vbox.pack_start(gtk.Label("Opacity"))
        scrollbar = gtk.HScrollbar()
        scrollbar.show()
        scrollbar.set_size_request(*self.SCROLLBARSIZE)
        scrollbar.set_range(0, 1)
        scrollbar.set_increments(.05, .2)
        scrollbar.set_value(1.0)
        scrollbar.connect('value_changed', self.change_opacity_of_surf)
        vbox.pack_start(scrollbar)
        self.scrollbar_opacity = scrollbar
        tmp = gtk.HBox()
        vbox.pack_start(tmp)
        tmp.pack_start(gtk.Label("Color"),False,False)
        self.color_chooser = ColorChooser()
        self.color_chooser.connect("color_changed",self.change_color_of_surf)
        tmp.pack_start(self.color_chooser,True,False)
        
        self.visibility_toggle = gtk.ToggleButton("Visible")
        vbox.pack_start(self.visibility_toggle, False, False)

        return expander

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
                            radius=shared.ratio*shared.marker_size)

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
            
    def _make_pipeline_expander(self):
        def decimate_toggled(button):
            frameDecimateFilter.set_sensitive(button.get_active())
            apply_()
        
        def connect_toggled(button):
            frameConnectFilter.set_sensitive(button.get_active())
            apply_()

        def set_connect_mode(id_):
            if self.paramd[id_].useConnect:
                for num in self.connectExtractButtons.keys():
                    bt = self.connectExtractButtons[num]
                    if bt.get_active():
                        self.paramd[id_].connect.mode = num
                        break

        def set_decimate_params(id_):
            if self.paramd[id_].useDecimate:
                self.paramd[id_].deci.targetReduction = self.scrollbar_target_reduction.get_value()

        def connect_method_changed(button):
            if button.get_active():
                apply_()

        def apply_(*args):
            id_ = self.__get_selected_id()
            self.paramd[id_].useConnect = self.buttonUseConnect.get_active()
            self.paramd[id_].useDecimate = self.buttonUseDecimate.get_active()
            
            set_connect_mode(id_)
            set_decimate_params(id_)
            pa = self.paramd[id_]
            print pa.deci.targetReduction
            self.paramd[id_].update_properties()
            self.render()

        expander = gtk.Expander('Pipeline settings')

        vbox = gtk.VBox()
        vbox.show()
        vbox.set_spacing(3)
        expander.add(vbox)

        self.vboxPipeline = vbox

        decattrs = DecimateFilter.labels.keys()
        decattrs.sort()
        self.decattrs = decattrs 

        names = self.paramd.keys()
        names.sort()

        # Filter selection
        framePipelineFilters = gtk.Frame('Pipeline filters')
        framePipelineFilters.set_border_width(5)
        vbox.pack_start(framePipelineFilters, True, True)
        vboxFrame = gtk.VBox()
        vboxFrame.set_spacing(3)
        framePipelineFilters.add(vboxFrame)
        self.buttonUseConnect = gtk.CheckButton('Use connect filter')
        self.buttonUseConnect.set_active(False)
        self.buttonUseConnect.connect('toggled', connect_toggled)
        vboxFrame.pack_start(self.buttonUseConnect, True, True)
        self.buttonUseDecimate = gtk.CheckButton('Use decimate filter')
        self.buttonUseDecimate.set_active(False)
        self.buttonUseDecimate.connect('toggled', decimate_toggled)
        vboxFrame.pack_start(self.buttonUseDecimate, True, True)

        #Connect filter settings
        frameConnectFilter = gtk.Frame('Connect filter settings')
        frameConnectFilter.set_border_width(5)
        frameConnectFilter.set_sensitive(False)
        vbox.pack_start(frameConnectFilter, True, True)
        vboxFrame = gtk.VBox()
        vboxFrame.set_spacing(3)
        frameConnectFilter.add(vboxFrame)
        extractModes = ConnectFilter.num2mode.items()
        extractModes.sort()
        lastButton = None
        self.connectExtractButtons = {}
        for num, name in extractModes:
            button = gtk.RadioButton(lastButton)
            button.set_label(name)
            if num==ConnectFilter.mode:
                button.set_active(True)
            button.connect("toggled",connect_method_changed)
            vboxFrame.pack_start(button, True, True)
            self.connectExtractButtons[num] = button
            lastButton = button

        #Decimate filter settings
        frameDecimateFilter = gtk.Frame('Decimate filter settings')
        frameDecimateFilter.set_border_width(5)
        frameDecimateFilter.set_sensitive(False)
        vbox.pack_start(frameDecimateFilter, True, True)
        vboxFrame = gtk.VBox()
        vboxFrame.set_spacing(3)
        vboxFrame.pack_start(gtk.Label("Target Reduction"))
        scrollbar = gtk.HScrollbar()
        scrollbar.show()
        scrollbar.set_size_request(*self.SCROLLBARSIZE)
        scrollbar.set_range(0, 0.99)
        scrollbar.set_increments(.05, .2)
        scrollbar.set_value(0.8)
        scrollbar.connect('value_changed', apply_)
        self.scrollbar_target_reduction = scrollbar
        vboxFrame.pack_start(scrollbar)
        frameDecimateFilter.add(vboxFrame)

        #button = gtk.Button(stock=gtk.STOCK_APPLY)
        #vbox.pack_start(button, True, True)
        #button.connect('clicked', apply)
        #expander.show_all()

        return expander

    def update_pipeline_params(self, *args):
        id_ = self.__get_selected_id()

        # set the active props of the filter frames
        self.buttonUseConnect.set_active(self.paramd[id_].useConnect)
        self.buttonUseDecimate.set_active(self.paramd[id_].useDecimate)
        connect_mode = self.paramd[id_].connect.mode
        print connect_mode
        activeButton = self.connectExtractButtons[connect_mode]
        activeButton.set_active(True)

        self.scrollbar_target_reduction.set_value(self.paramd[id_].deci.targetReduction)

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

        main_frame = gtk.Frame('Add segment')
        main_frame.set_border_width(5)
        self.inner_vbox.pack_start(main_frame, False,False)

        main_vbox = gtk.VBox()
        main_frame.add(main_vbox)

        frame = gtk.Frame('Intensity threshold')
        frame.set_border_width(5)
        main_vbox.pack_start(frame,False,False)

        
        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frame.add(vboxFrame)

        table = gtk.Table(1,2)
        table.set_col_spacings(3)
        table.show()
        vboxFrame.pack_start(table, True, True)        

        self.labelIntensity = gtk.Label('Value: ')
        self.labelIntensity.show()
        self.entryIntensity = gtk.Entry()
        self.entryIntensity.show()
        self.entryIntensity.set_text('%1.1f' % SurfParams.intensity)


        table.attach(self.labelIntensity, 0, 1, 0, 1,
                     xoptions=gtk.FILL, yoptions=0)
        table.attach(self.entryIntensity, 1, 2, 0, 1,
                     xoptions=gtk.EXPAND|gtk.FILL, yoptions=0)



        hbox = gtk.HBox()
        hbox.show()
        hbox.set_homogeneous(True)
        hbox.set_spacing(3)
        vboxFrame.pack_start(hbox, False, False)

        button = gtk.Button('Capture')
        button.show()
        button.connect('clicked', self.start_collect_intensity)
        hbox.pack_start(button, True, True)

        button = ButtonAltLabel('Stop', gtk.STOCK_STOP)
        button.show()
        button.connect('clicked', self.stop_collect_intensity)
        hbox.pack_start(button, True, True)

        button = ButtonAltLabel('Clear', gtk.STOCK_CLEAR)
        button.show()
        button.connect('clicked', self.clear_intensity)
        hbox.pack_start(button, True, True)

        frame.show_all()


        frame = gtk.Frame('Segment properties')
        frame.show()
        frame.set_border_width(5)
        main_vbox.pack_start(frame, False, False)

        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frame.add(vboxFrame)

        table = gtk.Table(2,2)
        table.set_col_spacings(3)
        table.set_row_spacings(3)
        table.show()
        vboxFrame.pack_start(table, True, True)

        self.labelName = gtk.Label('Label: ')
        self.labelName.show()
        self.labelName.set_alignment(xalign=1.0, yalign=0.5)
        self.entryName = gtk.Entry()
        self.entryName.show()
        self.entryName.set_text(SurfParams.label)

        table.attach(self.labelName, 0, 1, 0, 1,
                     xoptions=gtk.FILL, yoptions=0)
        table.attach(self.entryName, 1, 2, 0, 1,
                     xoptions=gtk.EXPAND|gtk.FILL, yoptions=0)


        def func(menuitem, *args):
            if shared.debug: print "option menu changed", menuitem
            s = menuitem.get_active_text()
            if s=='custom...':
                self.lastColor = self.choose_color()
            else:
                self.entryName.set_text(s)
                self.lastColor = colord[s]

        colors = [ name for name, color in colorSeq]
        colors.append('custom...')
        label = gtk.Label('Color: ')
        label.show()
        label.set_alignment(xalign=1.0, yalign=0.5)
        optmenu = make_option_menu(
            colors, func)
        optmenu.show()
        table.attach(label, 0, 1, 1, 2,
                     xoptions=gtk.FILL, yoptions=0)
        table.attach(optmenu, 1, 2, 1, 2,
                     xoptions=gtk.EXPAND|gtk.FILL, yoptions=0)

        button = ButtonAltLabel('Add segment', gtk.STOCK_ADD)
        button.show()
        button.connect('clicked', self.add_segment)
        main_vbox.pack_start(button, False, False)        

        frame.show_all()

        
    def _make_seqment_props_frame(self):
        """
        Control the sement attributes (delete, opacity, etc)
        """

        frame = gtk.Frame('Segment properties')
        frame.set_border_width(5)
        self.inner_vbox.pack_start(frame, False, False)

        
        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frame.add(vboxFrame)

        self.vboxSegPropsFrame = vboxFrame
        self.update_segments_frame() 

    def _make_picker_frame(self):
        """
        Controls to clean up the rendered segments
        """

        frame = gtk.Frame('Add marks only on ...')
        frame.show()
        frame.set_border_width(5)
        self.inner_vbox.pack_start(frame, False, False)

        vboxFrame = gtk.VBox()
        vboxFrame.show()
        vboxFrame.set_spacing(3)
        frame.add(vboxFrame)

        self.vboxPickerFrame = vboxFrame
        self.pickerName = None
        self.update_picker_frame() 

    def update_picker_frame(self):
        'Update the picker frame with the latest segments'

        # the name of the segment to be picked

        keys = self.paramd.keys()
        if len(keys) and self.pickerName is None:
            self.pickerName = keys[0]
        
        vbox = self.vboxPickerFrame
        
        widgets = vbox.get_children()
        for w in widgets:
            vbox.remove(w)

        names = self.paramd.keys()

        if not len(names):
            label = gtk.Label('No segments defined')
            label.show()
            vbox.pack_start(label)
            return
        
        names.sort()

        boxRadio = gtk.VBox()
        boxRadio.show()
        vbox.pack_start(boxRadio, True, True)

        def radio_changed(button):
            label = button.get_label()
            if label=='None': self.pickerName = None
            else: self.pickerName = label
            
        
        lastButton = None
        button = gtk.RadioButton(lastButton)
        button.set_label('None')
        button.set_active(True)
        button.connect('clicked', radio_changed)
        lastButton = button

        for name in names:
            button = gtk.RadioButton(lastButton)
            button.set_label(name)
            button.set_active(False)
            button.show()
            button.connect('clicked', radio_changed)
            boxRadio.pack_start(button, False, False)
            lastButton = button


    def clear_intensity(self, button):
        self.intensitySum = 0
        self.intensityCnt = 0
        self.entryIntensity.set_text('%1.1f' % SurfParams.intensity)        

    def start_collect_intensity(self, button):
        self.collecting = True

    def stop_collect_intensity(self, button):
        self.collecting = False

    def add_intensity(self, val):
        if self.collecting:
            self.intensitySum += val
            self.intensityCnt += 1

    def add_segment(self, button):
        self.nsurf +=1
        val = self.get_intensity()
        if val is None: return
        name = self.entryName.get_text()
        if not len(name):
            error_msg('You must enter a name in the Intensity tab')
            return

        tree_iter = self.tree_surf.append(None)
        self.tree_surf.set(tree_iter, 0,self.nsurf, 1, name)

        if not self.paramd.has_key(self.nsurf):
            self.paramd[self.nsurf] = SurfParams(self.sr.renderer, self.sr.interactor)

        params = self.paramd[self.nsurf]
        params.label = name
        params.intensity = val
        params.set_color(self.lastColor)
        params.set_image_data(self.sr.imageData)
        print "Add:", params.connect.mode
        params.update_properties()
        
        self.__update_treeview_visibility()
        #self.update_segments_frame() 
        #self.update_picker_frame()
        
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

    def choose_color(self, *args):
        dialog = gtk.ColorSelectionDialog('Choose segment color')
            
        colorsel = dialog.colorsel

        da = gtk.DrawingArea()
        cmap = da.get_colormap()

        r,g,b = [int(65535*val) for val in self.lastColor]
        color = cmap.alloc_color(r,g,b)
        colorsel.set_previous_color(color)
        colorsel.set_current_color(color)
        colorsel.set_has_palette(True)
    
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            color = colorsel.get_current_color()
            self.lastColor = [val/65535 for val in (color.red, color.green, color.blue)]

        dialog.destroy()
        return self.lastColor

    def __get_selected_id(self):
        treeiter = self.treev_sel.get_selected()[1]
        if treeiter:
            return self.tree_surf.get(treeiter,0)[0]
        else:
            return None

    def treev_sel_changed(self, selection):
        surf_id = self.__get_selected_id()
        if not surf_id:
            self.props_frame.hide()
            return

        self.props_frame.show_all()
        #print "selection changed", self.tree_roi.get(treeiter,0,1)
        try:
            self.color_chooser.color = gtk.gdk.Color(*(self.paramd[surf_id].color))
        except Exception, e:
            print "During setting color of color chooser:", type(e),e
        try:
            self.scrollbar_opacity.set_value(self.paramd[surf_id].opacity)
        except Exception, e:
            print "During setting value of opacity scrollbar:", type(e),e
        try:
            self.ignore_pipeline_updates = True
            self.update_pipeline_params()
        finally:
            self.ignore_pipeline_updates = False

    def change_opacity_of_surf(self,*args):
        surf_id = self.__get_selected_id()
        if not surf_id:
            return
        self.paramd[surf_id].set_opacity(self.scrollbar_opacity.get_value())
        self.render()

    def change_color_of_surf(self,*args):
        surf_id = self.__get_selected_id()
        if not surf_id:
            return
        self.paramd[surf_id].set_color(self.color_chooser.color)
        self.render()

    def __update_treeview_visibility(self):
        if self.tree_surf.get_iter_first()==None: 
            # tree is empty
            self.emptyIndicator.show()
            self.treev_surf.hide()
        else:
            self.emptyIndicator.hide()
            self.treev_surf.show()
