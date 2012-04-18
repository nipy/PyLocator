from __future__ import division

import gobject
import gtk

from gtkutils import error_msg, ButtonAltLabel
from dialogs import edit_label

from events import EventHandler

from colors import ColorChooserWithPredefinedColors, colorSeq

from list_toolbar import ListToolbar
from surf_params import SurfParams

from decimate_filter import DecimateFilter
from connect_filter import ConnectFilter

class SurfRendererProps(gtk.VBox):
    SCROLLBARSIZE = 150,20
    lastColor = SurfParams.color_
    lastColorName = SurfParams.colorName
    picker_surface_id = None
    pickerIdx = None
    imageData = None
    ignore_settings_updates = False

    paramd = {}   # a dict from ids (indices) to SurfParam instances

    def __init__(self):
        EventHandler().attach(self)
        self.nsurf=0

        gtk.VBox.__init__(self)
        self.show()
        self.set_homogeneous(False)

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
                 'Create a new iso-surface with default settings',
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

        hbox = gtk.HBox()
        hbox.show()
        vbox.pack_start(hbox, False)
        frame = self._make_color_chooser_frame()
        hbox.pack_start(frame, True, True)
        frame = self._make_picker_frame()
        hbox.pack_start(frame, True, True)
        
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

    def _make_picker_frame(self):
        frame = gtk.Frame("Insert markers")
        frame.show()
        self.pickerButton = gtk.ToggleButton("here!")
        self.pickerButton.connect("toggled", self.set_surface_for_picking)
        self.pickerButton.show()
        frame.add(self.pickerButton)
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
            if self.ignore_settings_updates:
                return
            id_ = self.__get_selected_id()
            self.paramd[id_].useConnect = self.buttonUseConnect.get_active()
            self.paramd[id_].useDecimate = self.buttonUseDecimate.get_active()
            
            set_connect_mode(id_)
            set_decimate_params(id_)
            pa = self.paramd[id_]
            pa.update_pipeline()
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

    def render(self, *args):
        EventHandler().notify("render now")

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
        if not self.imageData:
            error_msg("Cannot create surface. Image data of surface renderer is not set.")
            return
        if self.nsurf==0:
            self.__adjust_scrollbar_threshold_for_data()
        self.nsurf +=1

        intensity = self.__calculate_intensity_threshold()
        if intensity is None: return

        name = self.__create_segment_name(self.nsurf)
        if (not name) or name=="":
            return

        tree_iter = self.tree_surf.append(None)
        self.tree_surf.set(tree_iter, 0,self.nsurf, 1, name)
        
        self.__update_treeview_visibility()

        self.paramd[self.nsurf] = SurfParams(self.imageData, intensity, self.lastColor)
        params = self.paramd[self.nsurf]
        if self.nsurf==1:
            self.picker_surface_id = params.uuid
        params.label = name
        params.intensity = intensity
        params.set_color(self.lastColor, self.lastColorName)
        params.update_properties()

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
        min_, median_, max_ = EventHandler().get_nifti_stats()
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
            self.ignore_settings_updates = True
            self.scrollbar_threshold.set_value(param.intensity)
            if param.colorName==self.color_chooser.custom_str:
                self.color_chooser._set_color(param.color)
            else:
                self.color_chooser._set_color(param.colorName)
            self.scrollbar_opacity.set_value(param.opacity)
            self.update_pipeline_params()
            is_picker_surface = param.uuid==self.picker_surface_id
            self.pickerButton.set_active(is_picker_surface)
            self.pickerButton.set_sensitive(not is_picker_surface)
        except Exception, e:
            "During reacting to treeview selection change:", type(e), e
        finally:
            self.ignore_settings_updates = False

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

    def set_surface_for_picking(self, button, *args):
        if self.ignore_settings_updates:
            return
        param = self.__get_selected_surface()
        button.set_sensitive(False)
        self.picker_surface_id = param.uuid
        EventHandler().notify("set picker surface", param.uuid)

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

    def set_image_data(self, data):
        self.imageData = data

    def update_viewer(self, event, *args):
        if event=='set image data':
            self.set_image_data(args[0])
