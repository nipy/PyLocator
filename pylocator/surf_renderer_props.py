from __future__ import division
import sys, os
import vtk

import gobject
import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu
from dialogs import edit_label

from events import EventHandler, UndoRegistry
from markers import Marker
from shared import shared

from colors import ColorChooser, ColorChooserWithPredefinedColors, colord, colorSeq, tuple2gdkColor

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
    lastColorName = SurfParams.colorName

    paramd = {}   # a dict from ids (indices) to SurfParam instances

    def __init__(self, sr, pwxyz):
        """sr is a SurfRenderer"""

        self.nsurf=0
        self.pickerIdx=None
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
                 'Create a now iso-surface with default settings',
                 self.add_segment
                ],
                [gtk.STOCK_REMOVE, 
                 'Remove', 
                 'Remove selected surface',
                 self.cb_remove
                ],
                "-",
                [gtk.STOCK_BOLD, 
                 'name', 
                 'Edit name of surface',
                 self.cb_edit_name
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
        vboxProps.set_spacing(20)
        vboxProps.show()
        self.props_frame.add(vboxProps)
        general_expander = self._make_general_properties_expander()
        vboxProps.pack_start(general_expander, False)
        pipeline_expander = self._make_pipeline_expander()
        vboxProps.pack_start(pipeline_expander, False)

    def _make_general_properties_expander(self):
        expander = gtk.Expander('General settings')
        expander.set_expanded(True)
        expander.show()

        vbox = gtk.VBox()
        vbox.show()
        vbox.set_spacing(5)
        expander.add(vbox)

        frame = gtk.Frame("Threshold")
        frame.show()
        vbox.pack_start(frame)
        scrollbar = gtk.HScrollbar()
        scrollbar.set_update_policy(gtk.UPDATE_DELAYED)
        #scrollbar.set_draw_value(True)
        scrollbar.show()
        scrollbar.set_size_request(*self.SCROLLBARSIZE)
        scrollbar.set_range(0, 100)
        scrollbar.set_increments(1, 5)
        scrollbar.set_value(80)
        scrollbar.connect('value-changed', self.change_threshold_of_surf)
        self.scrollbar_threshold = scrollbar
        frame.add(scrollbar)

        frame = gtk.Frame("Opacity")
        frame.show()
        vbox.pack_start(frame)
        scrollbar = gtk.HScrollbar()
        scrollbar.set_update_policy(gtk.UPDATE_DELAYED)
        scrollbar.show()
        scrollbar.set_size_request(*self.SCROLLBARSIZE)
        scrollbar.set_range(0, 1)
        scrollbar.set_increments(.05, .2)
        scrollbar.set_value(1.0)
        scrollbar.connect('value-changed', self.change_opacity_of_surf)
        self.scrollbar_opacity = scrollbar
        frame.add(scrollbar)

        frame = self._make_color_chooser_frame()
        vbox.pack_start(frame)
        
        self.visibility_toggle = gtk.ToggleButton("Visible")
        vbox.pack_start(self.visibility_toggle, False, False)

        return expander
            
    def _make_color_chooser_frame(self):
        frame = gtk.Frame("Color")
        frame.show()
        self.color_chooser = ColorChooserWithPredefinedColors(colorSeq)
        self.color_chooser.connect("color_changed", self.change_color_of_surf)
        frame.add(self.color_chooser)
        return frame

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
            if self.ignore_pipeline_updates:
                return
            id_ = self.__get_selected_id()
            self.paramd[id_].useConnect = self.buttonUseConnect.get_active()
            self.paramd[id_].useDecimate = self.buttonUseDecimate.get_active()
            
            set_connect_mode(id_)
            set_decimate_params(id_)
            pa = self.paramd[id_]
            self.paramd[id_].update_pipeline()
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
        scrollbar.set_update_policy(gtk.UPDATE_DELAYED)
        scrollbar.show()
        scrollbar.set_size_request(*self.SCROLLBARSIZE)
        scrollbar.set_range(0, 0.99)
        scrollbar.set_increments(.05, .2)
        scrollbar.set_value(0.8)
        scrollbar.connect('value_changed', apply_)
        self.scrollbar_target_reduction = scrollbar
        vboxFrame.pack_start(scrollbar)
        frameDecimateFilter.add(vboxFrame)

        expander.show_all()
        return expander

    def key_press(self, interactor, event):
        key = interactor.GetKeySym()
        #XXX this is annoying in dwm (and probably elsewhere)
        #if self.pickerName is None:
            #error_msg('You must select the pick segment in the Picker tab')
            #return
        def checkPickerIdx():
            if self.pickerIdx is None:
                error_msg('Cannot insert marker. Choose surface first.')
                return False
            return True

        if key.lower()=='q': #hehehe
            gtk.main_quit()
        if key.lower()=='i':
            if not checkPickerIdx():
                return
            if shared.debug: print "Inserting Marker"
            x,y = interactor.GetEventPosition()
            print "e add1"
            picker = vtk.vtkCellPicker()
            picker.PickFromListOn()
            o = self.paramd[self.pickerIdx]
            print "e add2"
            picker.AddPickList(o.isoActor)
            print "e add2"
            picker.SetTolerance(0.005)
            print "e add2"
            picker.Pick(x, y, 0, self.sr.renderer)
            print "e add2"
            points = picker.GetPickedPositions()
            print "e add2"
            numPoints = points.GetNumberOfPoints()
            if numPoints<1: return
            pnt = points.GetPoint(0)

            marker = Marker(xyz=pnt,
                            rgb=EventHandler().get_default_color(),
                            radius=shared.ratio*shared.marker_size)
            print "e add3"
            EventHandler().add_marker(marker)
            print "e add4"
        elif key.lower()=='x':
            if not checkPickerIdx():
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

    def render(self, *args):
        self.sr.Render()

    def update_pipeline_params(self, *args):
        id_ = self.__get_selected_id()

        # set the active props of the filter frames
        self.buttonUseConnect.set_active(self.paramd[id_].useConnect)
        self.buttonUseDecimate.set_active(self.paramd[id_].useDecimate)
        connect_mode = self.paramd[id_].connect.mode
        activeButton = self.connectExtractButtons[connect_mode]
        activeButton.set_active(True)

        self.scrollbar_target_reduction.set_value(self.paramd[id_].deci.targetReduction)

    def add_segment(self, button):
        if self.nsurf==0:
            self.__adjust_scrollbar_threshold_for_data()
        self.nsurf +=1
        self.pickerIdx=self.nsurf

        intensity = self.__calculate_intensity_threshold()
        if intensity is None: return

        name = self.__create_segment_name(self.nsurf)
        if (not name) or name=="":
            return

        tree_iter = self.tree_surf.append(None)
        self.tree_surf.set(tree_iter, 0,self.nsurf, 1, name)

        self.paramd[self.nsurf] = SurfParams(self.sr.imageData, intensity, self.lastColor)
        params = self.paramd[self.nsurf]
        params.label = name
        params.intensity = intensity
        params.set_color(self.lastColor, self.lastColorName)
        params.update_properties()
        
        self.__update_treeview_visibility()

        self.render()
    
    def __calculate_intensity_threshold(self):
        min_, median_, max_ = EventHandler().get_nifti_stats()
        return median_
        
    def __create_segment_name(self, idx):
        return "Surface %i" % idx

    def interaction_event(self, observer, event):
        return
        #if not self.collecting: return 
        #xyzv = [0,0,0,0]
        #observer.GetCursorData(xyzv)
        #self.add_intensity(xyzv[3])
        #self.entryIntensity.set_text('%1.1f' % (self.intensitySum/self.intensityCnt))

    def __adjust_scrollbar_threshold_for_data(self):
        valid_increments = sorted([1.*10**e for e in range(-2,3)] +
                                    [2.*10**e for e in range(-2,3)] +
                                    [5.*10**e for e in range(-2,3)]
                                    )
        min_, max_, median_ = EventHandler().get_nifti_stats()
        incr1 = [i for i in valid_increments if i<(max_-min_)/100][-1]
        incr2 = [i for i in valid_increments if i<(max_-min_)/20][-1]
        self.scrollbar_threshold.set_range(min_, max_)
        self.scrollbar_threshold.set_increments(incr1, incr2)
        self.scrollbar_threshold.set_value(median_)

    def __get_selected_id(self):
        treeiter = self.treev_sel.get_selected()[1]
        if treeiter:
            return self.tree_surf.get(treeiter,0)[0]
        else:
            return None

    def __get_selected_surface(self):
        surf_id = self.__get_selected_id()
        if not surf_id:
            return None
        else:
            return self.paramd[surf_id]


    def treev_sel_changed(self, selection):
        param = self.__get_selected_surface()
        treeiter = self.treev_sel.get_selected()[1]
        if not treeiter:
            self.props_frame.hide()
            return
        self.props_frame.show()
        try:
            self.scrollbar_threshold.set_value(param.intensity)
        except Exception, e:
            print "During setting value of threshold scrollbar:", type(e),e
        try:
            if param.colorName==self.color_chooser.custom_str:
                self.color_chooser._set_color(param.color)
            else:
                self.color_chooser._set_color(param.colorName)
        except Exception, e:
            print "During setting color of color chooser:", type(e),e
        try:
            self.scrollbar_opacity.set_value(param.opacity)
        except Exception, e:
            print "During setting value of opacity scrollbar:", type(e),e
        try:
            self.ignore_pipeline_updates = True
            self.update_pipeline_params()
        finally:
            self.ignore_pipeline_updates = False

    def change_threshold_of_surf(self,*args):
        param = self.__get_selected_surface()
        if not param:
            return
        param.intensity = self.scrollbar_threshold.get_value()
        param.update_pipeline()
        self.render()

    def change_opacity_of_surf(self,*args):
        param = self.__get_selected_surface()
        param.set_opacity(self.scrollbar_opacity.get_value())
        self.render()

    def change_color_of_surf(self,*args):
        param = self.__get_selected_surface()
        self.lastColor = self.color_chooser.color
        self.lastColorName = self.color_chooser.colorName
        param.set_color(self.lastColor,self.lastColorName)
        self.render()

    def cb_remove(self, *args):
        surf_id = self.__get_selected_id()
        treestore, treeiter = self.treev_sel.get_selected()
        if treeiter:
            treestore.remove(treeiter)
            self.paramd[surf_id].destroy()
            del self.paramd[surf_id]
            self.__update_treeview_visibility()
            self.render()

    def cb_edit_name(self, *args):
        param = self.__get_selected_surface()
        new_name = edit_label(param.label, "Please enter a new name\nfor the selected surface")
        if not new_name or new_name==param.label: return
        param.label = new_name
        treeiter = self.treev_sel.get_selected()[1]
        if treeiter:
            return self.tree_surf.set(treeiter,1,str(new_name))

    def __update_treeview_visibility(self):
        if self.tree_surf.get_iter_first()==None: 
            # tree is empty
            self.emptyIndicator.show()
            self.treev_surf.hide()
        else:
            self.emptyIndicator.hide()
            self.treev_surf.show()
