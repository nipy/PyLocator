import gobject, gtk
import getopt,sys,os

from pylocator.controller import PyLocatorController
from pylocator.shared import shared

from nose.tools import assert_raises

def test_mainwindow_noargs():
    controller = PyLocatorController()
    controller.window.show()

#def test_mainwindow():
#    my_argv = ["-f", "somestrangeand_inexistent_file.nii.gz"]
#    options, args = getopt.getopt(my_argv[:], 'hf:s:', ['help','filename','surface'])
#    filename=None
#    surface=None
#    for option, value in options:
#        if option in ('-h', '--help'):
#            print usage; sys.exit(0)
#        if option in ('-f', '--file'):
#            filename=value
#        if option in ('-s', '--surface'):
#            surface=value
#
#    assert_raises(IOError,PyLocatorMainWindow,filename=filename,surface=surface)
