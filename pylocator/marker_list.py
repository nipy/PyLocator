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
        EventHandler().attach(self)
        self._markers = {}
        self.nmrk=0
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
        self.col3 = gtk.TreeViewColumn("Position",renderer,text=2)
        self.treev_mrk.append_column(self.col3)
        self.treev_mrk.show()
        self.scrolledwindow = gtk.ScrolledWindow()
        vbox.pack_start(self.scrolledwindow,True,True)
        self.scrolledwindow.add(self.treev_mrk)
        self.scrolledwindow.show()
        #Buttons for TreeView
        hbox = gtk.HBox()
        vbox.pack_start(hbox,False,False)
        button1 = gtk.Button(stock=gtk.STOCK_ADD)
        #button1.connect("clicked",self.add_mrk)
        hbox.pack_start(button1)
        button2 = gtk.Button(stock=gtk.STOCK_REMOVE)
        #button2.connect("clicked",self.rm_mrk)
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


    def update_viewer(self, event, *args):
        if event=='add marker':
            marker = args[0]
            self.add_marker(marker)
        elif event=='remove marker':
            marker = args[0]
            self.remove_marker(marker)
        #elif event=='color marker':
        #    marker, color = args
        #    marker.set_color(color)
        elif event=='label marker':
            marker, label = args
            print "MarkerList:", marker, label
            id_ = self._markers[marker.get_center()]
            treeiter = self._get_iter_for_id(id_)
            if treeiter:
                self.tree_mrk.set(treeiter,1,str(label))
        elif event=='move marker':
            marker, center = args
            x,y,z = marker.get_center()
            id_ = self._markers[marker.get_center()]
            treeiter = self._get_iter_for_id(id_)
            self.tree_mrk.set(treeiter,2,"%.1f,%.1f,%.1f"%(x,y,z))
        elif event=='select marker':
            marker = args[0]
        elif event=='unselect marker':
            marker = args[0]

    def _get_iter_for_id(self,id_):
        treeiter = self.tree_mrk.get_iter_first()
        while treeiter:
            print self.tree_mrk.get(treeiter,0)[0], id_
            if self.tree_mrk.get(treeiter,0)[0] == id_:
                break
            else:
                treeiter = self.tree_mrk.iter_next(treeiter)
        return treeiter

    def add_marker(self,marker):
        self.nmrk+=1
        self._markers[marker.get_center()] = self.nmrk
        x,y,z = marker.get_center()
        treeiter = self.tree_mrk.append(None)
        self.tree_mrk.set(treeiter,0,self.nmrk,1,"",2,"%.1f,%.1f,%.1f"%(x,y,z))

    def remove_marker(self,marker):
        try:
            id_ = self._markers[marker.get_center()]
            treeiter = self._get_iter_for_id(id_)
            if treeiter:
                self.tree_mrk.remove(treeiter)
                del self._markers[marker]
        except Exception, e:
            print "Exception in MarkerList.remove_marker"

    def treev_sel_changed(self,selection):
        pass
        #treeiter = selection.get_selected()[1]
        #if treeiter:
        #    self.props_frame.show_all()
        #    #print "selection changed", self.tree_roi.get(treeiter,0,1,2)
        #    roi_id = self.tree_roi.get(treeiter,0)
        #    try:
        #        self.color_chooser.color = gtk.gdk.Color(*(self.paramd[roi_id].color))
        #    except Exception, e:
        #        print "During setting color of color chooser:", type(e),e
        #    try:
        #        self.scrollbar_opacity.set_value(self.paramd[roi_id].opacity)
        #    except Exception, e:
        #        print "During setting value of opacity scrollbar:", type(e),e
        #else:
        #    self.props_frame.hide()

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

