import os

class Shared(object):
    debug = False
    lastSel = ''
    labels = ["L","R","P","A","I","S"]
    #lastSel = os.getcwd() + os.sep
    ratio = 3
    #screenshot_magnification = 3
    screenshot_cnt = 1

    planes_opacity = 1.
    markers_opacity = 1.
    marker_size = 3.

    lastLabel = ""

    def set_file_selection(self, name):
        """
        Set the filename or dir of the most recent file selected
        """
        self.lastSel = name

    def get_last_dir(self):
        """
        Return the dir name of the most recent file selected
        """
        if os.path.isdir(self.lastSel):
            return self.lastSel
        else:
            return os.path.dirname(self.lastSel) + os.sep



        

shared = Shared()
