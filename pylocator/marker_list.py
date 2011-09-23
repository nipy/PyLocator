from __future__ import division
import sys, os
import vtk

import gobject
import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu

from events import EventHandler, UndoRegistry, Viewer
from markers import Marker
from shared import shared


class MarkerList(gtk.Frame):
    """
    CLASS: MarkerList
    DESCR: 
    """
    paramd = {}   # a dict from names to SurfParam instances

    def __init__(self):
        super(MarkerList,self).__init__(self)
        self.set_label("List of markers")
        vbox = gtk.VBox()
        self.add(vbox)
        self.show_all()

        # action area
        hbox = gtk.HBox()
        hbox.show()
        vbox.pack_start(hbox, False, False)        


        #button = gtk.Button(stock=gtk.STOCK_CANCEL)
        #button.show()
        #button.connect('clicked', hide)
        #hbox.pack_start(button, True, True)        

            
        #button = ButtonAltLabel('Render', gtk.STOCK_EXECUTE)
        #button.show()
        #button.connect('clicked', self.render)
        #hbox.pack_start(button, True, True)        

        #button = gtk.Button(stock=gtk.STOCK_OK)
        #button.show()
        #button.connect('clicked', hide)
        #hbox.pack_start(button, True, True)        
        
        #create TreeView
        #Fields: Index, Short filename, long FN, is_active?, opacityi
        self.tree_mrk = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.nmrk = 0
        self.treev_mrk = gtk.TreeView(self.tree_mrk)
        self._treev_sel = self.treev_mrk.get_selection()
        self._treev_sel.connect("changed",self.treev_sel_changed)
        self._treev_sel.set_mode(gtk.SELECTION_SINGLE)
        renderer = gtk.CellRendererText()
        renderer.set_property("xalign",1.0)
        #renderer.set_xalign(0.0)
        self.col1 = gtk.TreeViewColumn("#",renderer,text=0)
        self.treev_mrk.append_column(self.col1)
        self.col2 = gtk.TreeViewColumn("Label",renderer,text=1)
        self.treev_mrk.append_column(self.col2)
        self.treev_mrk.show()
        vbox.pack_start(self.treev_mrk,True,True)
        #Buttons for TreeView
        hbox = gtk.HBox()
        vbox.pack_start(hbox,False,False)
        button1 = gtk.Button(stock=gtk.STOCK_ADD)
        button1.connect("clicked",self.add_mrk)
        hbox.pack_start(button1)
        button2 = gtk.Button(stock=gtk.STOCK_REMOVE)
        button2.connect("clicked",self.rm_mrk)
        hbox.pack_start(button2)
        hbox.show_all()

        ##Edit properties of one ROI
        #self.props_frame = gtk.Frame('Properties')
        #self.props_frame.set_border_width(5)
        #vboxFrame.pack_start(self.props_frame,False,False)
        #vboxProps = gtk.VBox()
        #self.props_frame.add(vboxProps)
        #vboxProps.pack_start(gtk.Label("Opacity"))
        #self.scrollbar_opacity = gtk.HScrollbar()
        #self.scrollbar_opacity.show()
        #self.scrollbar_opacity.set_size_request(*self.SCROLLBARSIZE)
        #self.scrollbar_opacity.set_range(0, 1)
        #self.scrollbar_opacity.set_increments(.05, .2)
        #self.scrollbar_opacity.set_value(1.0)
        #self.scrollbar_opacity.connect('value_changed', self.change_opacity_of_roi)
        #vboxProps.pack_start(self.scrollbar_opacity)
        #tmp = gtk.HBox()
        #vboxProps.pack_start(tmp)
        #tmp.pack_start(gtk.Label("Color"),False,False)
        #self.color_chooser = ColorChooser()
        #self.color_chooser.connect("color_changed",self.change_color_of_roi)
        #tmp.pack_start(self.color_chooser,True,False)


        #vboxProps.pack_start()
        #vboxProps.show_all()
        self.show_all()
        self.set_size_request(0,0)


    def add_mrk(self,*args):
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
            except IOError:
                error_msg(
                    'Could not load ROI mask from %s' % fname, 
                    )
            
            else:
                shared.set_file_selection(fname)
        else: dialog.destroy()

    def rm_mrk(self,*args):
        treestore,treeiter = self._treev_sel.get_selected()
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
        treeiter = self._treev_sel.get_selected()[1]
        if treeiter:
            roi_id = self.tree_roi.get(treeiter,0)
            self.paramd[roi_id].set_color(self.color_chooser.color)

    def change_opacity_of_roi(self,*args):
        treeiter = self._treev_sel.get_selected()[1]
        if treeiter:
            roi_id = self.tree_roi.get(treeiter,0)
            self.paramd[roi_id].set_opacity(self.scrollbar_opacity.get_value())

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
