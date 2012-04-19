Installation
============

.. index:: dependencies

Dependencies
-------------
PyLocator relies on a bunch of libraries:

* `VTK <http://www.vtk.org>`_: 3d-visualization
* `nibabel <http://nipy.sourceforge.net/nibabel/>`_: Reading the Nifti-format for MRI data
* `NumPy <http://www.scipy.org>`_: Sophisticated array-types for Python
* `GTK+ <http://www.pygtk.org/>`_: For the GUI.
* `GTK+ OpenGL Extension <http://projects.gnome.org/gtkglext/>`_

On a Debian-like environement, these dependencies can usually be resolved via a simple::

  sudo apt-get install python-vtk python-nibabel python-numpy python-gtk2 python-gtkglext1

This should prepare your system for PyLocator. On Windows and OS X, things are a little bit 
more complicated, but Python distributions like `EPD <http://www.enthought.com/products/epd.php>`_
or `Python(x,y) <http://www.pythonxy.com/>`_ should be helpful here. The main problem will be to 
get **gtkgtlext** working. If you have any hints, e.g., binary packages, please let me know.

Depending on your configuration, nibabel has to be downloaded separately.

Can you help with detailed instructions for these operating systems? Please tell me!


How to download
---------------
The source code of PyLocator is kept in a public GIT repository:

http://www.github.com/nipy/PyLocator

.. index:: repository
.. index:: source code

You can simply clone this repository via::

  git clone git://github.com/nipy/PyLocator.git

Alternatively, you can download a tarball that is updated once in a while from

http://pylocator.thorstenkranz.de/download/pylocator-1.0.beta.dev.tar.gz

Extract this archive using your preferred archive manager or in a terminal using something like::

  tar xfvz pylocator-1.0.beta.dev.tar.gz

How to install
---------------
From PyPI
^^^^^^^^^^^^^^^^^^^^
PyLocator is registered at PyPI, the Python Package Index. This makes 
installation easy. If you have setuptools installed, simply type::

    sudo easy_install PyLocator

and the setuptools will do the magic for you.

From source
^^^^^^^^^^^^^^^^^^^^
Once you obtained the source code, enter the PyLocator-directory and type::

  python setup.py build
  python setup.py install --user # For per-user installation
  # or
  sudo python setup.py install # system-wide installation

After these steps, the package *pylocator* should be properly installed. You can then run the program
by running::

  python ~/.local/lib/python2.?/site-packages/pylocator/pylocator.py

in case of a per-user installation or::

  python /usr/local/lib/python2.?/site-packages/pylocator/pylocator.py

or similar in case of a system-wide installation. Replace the *2.?* by your python version number. 

This solution isn't perfect yet, I'll clean it up soon. Of course you can create some little bash-script 
that calls this for you and put it into ~/bin/pylocator or similar::

  #! /bin/bash
  python ~/.local/lib/python2.?/site-packages/pylocator/pylocator.py $@



