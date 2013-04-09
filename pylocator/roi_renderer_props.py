from __future__ import division
import os.path
import gobject
import gtk
from gtkutils import error_msg, ButtonAltLabel

from events import EventHandler
from shared import shared

from surf_params import SurfParams

from list_toolbar import ListToolbar
from colors import ColorChooser
from vtkNifti import vtkNiftiImageReader
from rois import RoiParams
from dialogs import select_existing_file

from misc import persistence

class RoiRendererProps(gtk.VBox):
    SCALESIZE = 150,40
    lastColor = SurfParams.color
    paramd = {}   # a dict from names to SurfParam instances

    def __init__(self):
        gtk.VBox.__init__(self)
        self.show()

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
        EventHandler().notify("render now")
            
    def __create_toolbar(self):
        conf = [
                [gtk.STOCK_ADD,
                 'Add',
                 'Load ROI from file and render it',
                 self.cb_add_roi
                ],
                [gtk.STOCK_REMOVE, 
                 'Remove', 
                 'Remove selected ROI',
                 self.rm_roi
                ],
                "-",
                [gtk.STOCK_OPEN, 
                 'Load', 
                 'Load ROI settings from a file. Will discard all currently used ROIs',
                 self.load_rois
                ],
                [gtk.STOCK_SAVE_AS, 
                 'Save', 
                 'Save all ROI settings to a file.',
                 self.save_rois
                ],
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
        renderer.set_property("xalign",0.0)
        #renderer.set_xalign(0.0)
        #self.col1 = gtk.TreeViewColumn("#",renderer,text=0)
        #self.treev_roi.append_column(self.col1)
        self.col1 = gtk.TreeViewColumn("Short filename",renderer,text=1)
        self.treev_roi.append_column(self.col1)
        #self.treev_roi.show()
        self.inner_vbox.pack_start(self.treev_roi, False)

        #Empty-indicator
        self.emptyIndicator = gtk.Label('No region-of-interest defined')
        self.emptyIndicator.show()
        self.inner_vbox.pack_start(self.emptyIndicator, False)

        #Edit properties of one ROI
        self.props_frame = self._make_properties_frame()
        self.inner_vbox.pack_start(self.props_frame,False,False)

        #vboxProps.pack_start()

    def _make_properties_frame(self):
        frame = gtk.Frame('Properties')
        frame.set_border_width(5)
        vboxProps = gtk.VBox()
        frame.add(vboxProps)
        f1 = gtk.Frame("Opacity")
        f1.show()
        vboxProps.pack_start(f1, False)
        self.scale_opacity = gtk.HScale()
        self.scale_opacity.set_update_policy(gtk.UPDATE_DELAYED)
        self.scale_opacity.show()
        self.scale_opacity.set_size_request(*self.SCALESIZE)
        self.scale_opacity.set_range(0, 1)
        self.scale_opacity.set_increments(.05, .2)
        self.scale_opacity.set_value(1.0)
        self.scale_opacity.connect('value_changed', self.change_opacity_of_roi)
        f1.add(self.scale_opacity)

        f2 = gtk.Frame("Color")
        f2.show()
        vboxProps.pack_start(f2, False)
        tmp = gtk.HBox()
        f2.add(tmp)
        self.color_chooser = ColorChooser()
        self.color_chooser.connect("color_changed",self.change_color_of_roi)
        tmp.pack_start(self.color_chooser,True,False)
        vboxProps.show_all()
        return frame

    def cb_add_roi(self,*args):
        fname = select_existing_file('Choose filename for ROI mask')
        try:
            if fname is not None:
                self._do_add_roi(fname)
            shared.set_file_selection(fname)
        except IOError:
            error_msg(
                'Could not load ROI mask from %s' % fname, 
                )
        finally:
            self.__update_treeview_visibility()
        self.render()

    def _do_add_roi(self, fname, *args):
        self.nroi+=1
        tree_iter = self.tree_roi.append(None)
        self.tree_roi.set(tree_iter,0,self.nroi,1,os.path.split(fname)[1],2,fname,3,True)
        self.__update_treeview_visibility()

        roi_image_reader = vtkNiftiImageReader()
        roi_image_reader.SetFileName(fname)
        roi_image_reader.Update()
        roi_id = self.tree_roi.get(tree_iter,0) 
        self.paramd[roi_id] = RoiParams(roi_image_reader, *args)
        return roi_id
        #self.paramd[roi_id].update_pipeline()
        #print self.paramd[roi_id].intensity
                
    def rm_roi(self,*args):
        treestore,treeiter = self.treev_sel.get_selected()
        roi_id = treestore.get(treeiter,0)
        treestore.remove(treeiter)
        self.paramd[roi_id].destroy()
        del self.paramd[roi_id]
        self.__update_treeview_visibility()
        self.render()
        
    def save_rois(self,*args):
        if len(self.paramd.keys())==0:
            error_msg("Cannot save to file as no ROIs are defined yet.",self.get_toplevel(),title="Not possible" )
            return
            
        rois = [dict(absolute_path=os.path.abspath(roi.image.GetFilename()),
                     relative_path=os.path.relpath(roi.image.GetFilename()),
                     opacity=roi.opacity, color=roi.color) for roi in self.paramd.values()]
        
        def ok_clicked(w):
            fname = dialog.get_filename()
            shared.set_file_selection(fname)
            try: 
                persistence.save_rois(rois, fname)
            except IOError:
                error_msg('Could not save data to %s' % fname,
                          )
            else:
                dialog.destroy()

        dialog = gtk.FileSelection('Choose filename for ROIs')
        dialog.set_filename(shared.get_last_dir())
        dialog.ok_button.connect("clicked", ok_clicked)
        dialog.cancel_button.connect("clicked", lambda w: dialog.destroy())
        dialog.show()
        
    def load_rois(self, *args):
        filename = select_existing_file("Please choose the file containing ROIs")
        if filename is None:
            return
        rois = persistence.load_rois(filename)
        self._precheck_rois_sanity() 
        self._clear_all_rois()
        for roi in rois["Data"]:
            if (self._relpath_exists(roi)):
                self._do_add_roi(roi["relative_path"], roi["color"], roi["opacity"])
            elif (self._abspath_exists(roi)):
                self._do_add_roi(roi["absolute_path"], roi["color"], roi["opacity"])       
            else:
                error_msg("Cannot load ROIs from file. Path to Nifti is not valid." + \
                          "Searched at: \n%s and \n%s" % (roi["relative_path"], roi["absolut_path"]),
                          self.get_toplevel(),title="Loading failed")
                return
        self.render()
    
    def _relpath_exists(self, roi):
        path = roi["relative_path"]
        return os.path.isfile(path)
        
    def _abspath_exists(self, roi):
        path = roi["absolute_path"]
        return os.path.isfile(path)
    
    def _clear_all_rois(self):
        self.tree_roi.clear()
        for k in self.paramd.keys():
            self.paramd[k].destroy()
            del self.paramd[k]
        self.nroi = 0
        
    def _precheck_rois_sanity(self):
        pass
    
#    def _set_properties_for_roi(self, roi_id, roi_dict):
#        roi = self.paramd[roi_id]
#        print "_set_properties_for_roi:", roi.uuid
#        roi.set_opacity(roi_dict["opacity"])
#        roi.set_color(roi_dict["color"])

    def treev_sel_changed(self,selection):
        treeiter = selection.get_selected()[1]
        if treeiter:
            self.props_frame.show_all()
            #print "selection changed", self.tree_roi.get(treeiter,0,1,2)
            roi_id = self.tree_roi.get(treeiter,0)
            try:
                self.color_chooser._set_color(self.paramd[roi_id].color)
            except Exception, e:
                print "During setting color of color chooser:", type(e),e
            try:
                self.scale_opacity.set_value(self.paramd[roi_id].opacity)
            except Exception, e:
                print "During setting value of opacity scale:", type(e),e
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
            self.paramd[roi_id].set_opacity(self.scale_opacity.get_value())
            self.render()

    def __update_treeview_visibility(self):
        if self.tree_roi.get_iter_first()==None: 
            # tree is empty
            self.emptyIndicator.show()
            self.treev_roi.hide()
        else:
            self.emptyIndicator.hide()
            self.treev_roi.show()

