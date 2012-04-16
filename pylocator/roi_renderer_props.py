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

from surf_params import SurfParams

from list_toolbar import ListToolbar
from decimate_filter import DecimateFilter
from connect_filter import ConnectFilter
from colors import ColorChooser, colord, colorSeq
from vtkNifti import vtkNiftiImageReader

class RoiParams(SurfParams):
    intensity = 0.5

    def set_lighting(self):
        surf_prop = self.isoActor.GetProperty()
        surf_prop.SetAmbient(.2)
        surf_prop.SetDiffuse(.3)
        surf_prop.SetSpecular(.5)

class RoiRendererProps(gtk.VBox):
    """
    CLASS: RoiRendererProps
    DESCR: 
    """

    SCROLLBARSIZE = 150,20
    lastColor = SurfParams.color
    paramd = {}   # a dict from names to SurfParam instances

    def __init__(self, sr, pwxyz):
        """sr is a SurfRenderer"""
        gtk.VBox.__init__(self)
        self.show()

        self.sr = sr
        self.pwxyz = pwxyz
        self.interactorStyle = self.sr.GetInteractorStyle()

        toolbar = self.__create_toolbar()
        self.pack_start(toolbar,False,False)

        self.scrolled_window = gtk.ScrolledWindow()

        self.inner_vbox = gtk.VBox()
        self.inner_vbox.set_spacing(20)
        self.scrolled_window.add_with_viewport(self.inner_vbox)
        self.pack_start(self.scrolled_window)
        self.scrolled_window.show_all()

        self._make_roi_list()
            
        button = ButtonAltLabel('Render', gtk.STOCK_EXECUTE)
        button.show()
        button.connect('clicked', self.render)
        self.pack_end(button, False, False)        
        self.__update_treeview_visibility()


    def render(self, *args):
        self.pwxyz.Render()
        self.sr.Render()
            
    def __create_toolbar(self):
        conf = [
                [gtk.STOCK_ADD,
                 'Add',
                 'Load ROI from file and render it',
                 self.add_roi
                ],
                [gtk.STOCK_REMOVE, 
                 'Remove', 
                 'Remove selected ROI',
                 self.rm_roi
                ],
                #"-",
                #[gtk.STOCK_GO_UP, 
                # 'Move up', 
                # 'Move selected marker up in list',
                # self.cb_move_up
                #],
                #[gtk.STOCK_GO_DOWN, 
                # 'Move down', 
                # 'Move selected marker down in list',
                # self.cb_move_down
                #],
               ]
        return ListToolbar(conf)

    def _make_roi_list(self):
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
        #self.treev_roi.show()
        self.inner_vbox.pack_start(self.treev_roi)

        #Empty-indicator
        self.emptyIndicator = gtk.Label('No region-of-interest defined')
        self.emptyIndicator.show()
        self.inner_vbox.pack_start(self.emptyIndicator, False)

        #Edit properties of one ROI
        self.props_frame = gtk.Frame('Properties')
        self.props_frame.set_border_width(5)
        self.inner_vbox.pack_start(self.props_frame,False,False)
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
                    self.paramd[roi_id] = RoiParams([self.sr.renderer,self.pwxyz.renderer], self.sr.interactor)
                    self.paramd[roi_id].set_image_data(roi_image_reader.GetOutput())
                    self.paramd[roi_id].update_pipeline()
                    print self.paramd[roi_id].intensity
                    self.sr.Render()
                shared.set_file_selection(fname)
            except IOError:
                error_msg(
                    'Could not load ROI mask from %s' % fname, 
                    )
            finally:
                self.__update_treeview_visibility()
        else: dialog.destroy()
        self.render()

    def rm_roi(self,*args):
        treestore,treeiter = self.treev_sel.get_selected()
        roi_id = treestore.get(treeiter,0)
        treestore.remove(treeiter)
        self.paramd[roi_id].destroy()
        del self.paramd[roi_id]
        self.__update_treeview_visibility()
        self.render()

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
            self.render()

    def change_opacity_of_roi(self,*args):
        treeiter = self.treev_sel.get_selected()[1]
        if treeiter:
            roi_id = self.tree_roi.get(treeiter,0)
            self.paramd[roi_id].set_opacity(self.scrollbar_opacity.get_value())
            self.render()

    def __update_treeview_visibility(self):
        if self.tree_roi.get_iter_first()==None: 
            # tree is empty
            self.emptyIndicator.show()
            self.treev_roi.hide()
        else:
            self.emptyIndicator.hide()
            self.treev_roi.show()
