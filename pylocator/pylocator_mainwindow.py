#! /usr/bin/python

import gobject, gtk
import getopt,sys,os
import os.path

from .plane_widgets import PlaneWidgetsWithObservers
from .shared import shared

class PyLocatorMainWindow(gtk.Window):
    """Main window class"""

    def __init__(self,title="PyLocator",filename=None,surface=None):
        if filename:
            title=title+" - "+filename
        gtk.Window.__init__(self)
        self.set_title(title)
        self.connect("destroy", self._quit)
        self.connect("delete_event", self._quit)
        self.set_border_width(10)
        self.set_size_request(900, 600)  #w,h
        self.show()

        self.pwo = PlaneWidgetsWithObservers(self)
        self.pwo.show()
        self.add(self.pwo)

        user_dir = self.find_userdir()
        shared.set_file_selection(user_dir)

        if filename:
            #test for filename
            if os.path.isfile(filename):
                self.pwo.mainToolbar.niftiFilename=filename
                def niftiidle(*args):
                    self.pwo.mainToolbar.load_mri()
                    if surface:
                        #implement auto surface rendering, good for thorsten
                        pass
                    return False
                gobject.idle_add(niftiidle)
            else:
                raise IOError("No such file or directory: %s"%filename)
                

    def _quit(self,*args):
        self.pwo.destroy()
        gtk.main_quit()

    def find_userdir(self):
        userdir = os.path.expanduser("~")
        try:
            from win32com.shell import shellcon, shell
            userdir = shell.SHGetFolderPath(0,shellcon.CSIDL_PERSONAL,0,0)
        except ImportError,ie:
            userdir = os.path.expanduser("~")
        return userdir

