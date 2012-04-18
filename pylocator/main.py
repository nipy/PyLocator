#! /usr/bin/python

import gtk
import os.path
from controller import PyLocatorController
from shared import shared

def run_pylocator(filename=None, surface=None):
    """main method to run when PyLocator is started"""
    __global_preparations()
    controller = PyLocatorController()
    loadingSuccessful = controller.load_nifti(filename)
    controller.align_surf_to_planes_view()
    if loadingSuccessful:
        controller.window.show()
        gtk.main()

def __global_preparations():
    user_dir = __find_userdir()
    shared.set_file_selection(user_dir)


def __find_userdir():
    userdir = os.path.expanduser("~")
    try:
        from win32com.shell import shellcon, shell
        userdir = shell.SHGetFolderPath(0,shellcon.CSIDL_PERSONAL,0,0)
    except ImportError:
        userdir = os.path.expanduser("~")
    return userdir

if __name__=="__main__":
    run_pylocator()
