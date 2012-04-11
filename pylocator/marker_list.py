from __future__ import division
import sys, os
import vtk

import gobject
import gtk
from gtk import gdk

from gtkutils import error_msg, simple_msg, ButtonAltLabel, \
     str2posint_or_err, str2posnum_or_err, ProgressBarDialog, make_option_menu, get_three_nums

from dialogs import edit_coordinates

from events import EventHandler, UndoRegistry, Viewer
from colors import choose_one_color, tuple2gdkColor, gdkColor2tuple
from markers import Marker
from marker_list_toolbar import MarkerListToolbar
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
        self._marker_ids = {}
        self.nmrk=0
        self.set_label("List of markers")
        vbox = gtk.VBox()
        self.add(vbox)
        self.show_all()

        # action area
        hbox = gtk.HBox()
        hbox.show()
        vbox.pack_start(hbox, False, False)        
        
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

        #Toolbar
        toolbar = MarkerListToolbar(self)
        vbox.pack_start(toolbar,False,False)

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
            #print "MarkerList:", marker.uuid, label
            id_ = self._marker_ids[marker.uuid]
            treeiter = self._get_iter_for_id(id_)
            if treeiter:
                self.tree_mrk.set(treeiter,1,str(label))
        elif event=='move marker':
            marker, center = args
            x,y,z = center #marker.get_center()
            id_ = self._marker_ids[marker.uuid]
            treeiter = self._get_iter_for_id(id_)
            self.tree_mrk.set(treeiter,2,"%.1f,%.1f,%.1f"%(x,y,z))
        elif event=='select marker':
            marker = args[0]
        elif event=='unselect marker':
            marker = args[0]

    def cb_add(self,*args):
        parent_window = self.get_parent_window()
        #print parent_window
        coordinates = edit_coordinates(description="Please enter the coordinates\nfor the marker to be added")
        if coordinates==None:
            return
        x,y,z = coordinates
        marker = Marker(xyz=(x,y,z),
                        rgb=EventHandler().get_default_color(),
                        radius=shared.ratio*3)

        EventHandler().add_marker(marker)


    def cb_remove(self,*args):
        treeiter = self._treev_sel.get_selected()[1]
        if treeiter:
            mrk_id = self.tree_mrk.get(treeiter,0)[0]
            EventHandler().remove_marker(self._markers[mrk_id])

    def cb_choose_color(self,*args):
        treeiter = self._treev_sel.get_selected()[1]
        if not treeiter:
            return
        mrk_id = self.tree_mrk.get(treeiter,0)[0]
        marker = self._markers[mrk_id]
        old_color = marker.get_color()
        print old_color
        new_color = choose_one_color("New color for marker",tuple2gdkColor(old_color))
        print new_color
        EventHandler().notify('color marker', marker, gdkColor2tuple(new_color))

    def cb_move_up(self, *args):
        self._move_in_list(up=True)

    def cb_move_down(self, *args):
        self._move_in_list(up=False)

    def cb_edit_position(self,*args):
        treeiter = self._treev_sel.get_selected()[1]
        if treeiter:
            mrk_id = self.tree_mrk.get(treeiter,0)[0]
        marker = self._markers[mrk_id]
        x_old,y_old,z_old = marker.get_center()
        #parent_window = self.get_parent_window()
        #print parent_window
        coordinates = edit_coordinates(x_old,y_old,z_old)
        if coordinates==None:
            return
        x,y,z = coordinates
        EventHandler().notify("move marker",marker, (x,y,z))
        self.treev_sel_changed(self._treev_sel)


    def _move_in_list(self,up=True):
        if self._treev_sel.count_selected_rows == 0:
            return
        ( model, rows ) = self._treev_sel.get_selected_rows()
        # Get new path for each selected row and swap items. */
        for path1 in rows:
            # Move path2 in right direction
            if up:
                path2 = ( path1[0] - 1, )
            else:
                path2 = ( path1[0] + 1, )
            # If path2 is negative, we're trying to move first path up. Skip
            # one loop iteration.
            if path2[0] < 0:
                continue
            # Obtain iters and swap items. If the second iter is invalid, we're
            # trying to move the last item down. */
            iter1 = model.get_iter( path1 )
            try:
                iter2 = model.get_iter( path2 )
            except ValueError:
                continue
            model.swap( iter1, iter2 )

    def _get_iter_for_id(self,id_):
        treeiter = self.tree_mrk.get_iter_first()
        while treeiter:
            #print self.tree_mrk.get(treeiter,0)[0], id_
            if self.tree_mrk.get(treeiter,0)[0] == id_:
                break
            else:
                treeiter = self.tree_mrk.iter_next(treeiter)
        return treeiter

    def add_marker(self,marker):
        self.nmrk+=1
        self._marker_ids[marker.uuid] = self.nmrk
        self._markers[self.nmrk]=marker
        x,y,z = marker.get_center()
        treeiter = self.tree_mrk.append(None)
        self.tree_mrk.set(treeiter,0,self.nmrk,1,"",2,"%.1f,%.1f,%.1f"%(x,y,z))

    def remove_marker(self,marker):
        try:
            id_ = self._marker_ids[marker.uuid] 
            treeiter = self._get_iter_for_id(id_)
            if treeiter:
                self.tree_mrk.remove(treeiter)
                del self._markers[id_]
                del self._marker_ids[marker.uuid]
        except Exception, e:
            print "Exception in MarkerList.remove_marker"

    def treev_sel_changed(self,selection):
        EventHandler().clear_selection()
        try:
            treeiter = selection.get_selected()[1]
            if treeiter:
                mrk_id = self.tree_mrk.get(treeiter,0)[0]
                if mrk_id==None:
                    return
                marker = self._markers[mrk_id]
                EventHandler().select_new(marker)
        except:
            pass

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

