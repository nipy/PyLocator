# -*- coding: utf-8 -*-
"""
Small helper methods.
"""

import os

def relative_and_absolute_path(path):
    """Takes a relative or absolute path and returns both the relative and the 
    absolute path, with respect to the current"""
    return os.path.relpath(path), os.path.abspath(path)
    
