#! /usr/bin/python

import gobject, gtk
import getopt,sys,os

from plane_widgets import PlaneWidgetsWithObservers
from shared import shared

usage="""usage: %s [options]
options:
--help -h         print this message
--filename -f     filename""" % sys.argv[0]

def main(*args):
    try:
        options, args = getopt.getopt(sys.argv[1:], 'hf:s:', ['help','filename=','surface'])
    except (getopt.GetoptError):
            print usage; sys.exit(0)

    filename=None
    surface=None

    for option, value in options:
        if option in ('-h', '--help'):
            print usage; sys.exit(0)
        if option in ('-f', '--file'):
            filename=value
        if option in ('-s', '--surface'):
            surface=value

    title="PyLocator"
    if filename:
        title=title+" - "+filename


    window = gtk.Window()
    window.set_title(title)
    window.connect("destroy", gtk.main_quit)
    window.connect("delete_event", gtk.main_quit)
    window.set_border_width(10)
    window.set_size_request(640, 480)  #w,h
    window.show()

    pwo = PlaneWidgetsWithObservers(window)
    pwo.show()
    window.add(pwo)

    shared.set_file_selection(os.getcwd())

    def idle(*args):
        pwo.mainToolbar.load_image()
        return False

    if filename:
        #test for filename
        if os.path.isfile(filename):
            pwo.mainToolbar.niftiFilename=filename
            def niftiidle(*args):
                pwo.mainToolbar.load_mri()
                if surface:
                    #implement auto surface rendering, good for thorsten
                    pass
                return False
            gobject.idle_add(niftiidle)
        else:
            print "no such file or directory:",filename
            sys.exit(1)

        
    #gobject.idle_add(idle)

    gtk.main()

if __name__=="__main__":
    main()
