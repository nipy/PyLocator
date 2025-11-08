Installation
============

Dependencies
------------

PyLocator now relies on a modern Qt/VTK stack:

* `VTK <https://vtk.org>`_ for 3-D visualisation
* `Nibabel <https://nipy.org/nibabel>`_ for reading NIfTI volumes
* `NumPy <https://numpy.org>`_ for numerical data handling
* `PySide6 <https://wiki.qt.io/Qt_for_Python>`_ for the Qt user interface

The recommended way to install these dependencies is via ``pip`` inside a
Python 3.11 virtual environment::

  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

Running ``pip install -e .`` afterwards exposes the ``pylocator`` console entry
point and keeps the working copy editable.

How to download
---------------

The source code lives on GitHub::

  git clone https://github.com/nipy/PyLocator.git

You can use the repository directly for development or installation.

How to install
--------------

From PyPI
^^^^^^^^^

The PyPI package can be installed with::

  pip install pylocator

From source
^^^^^^^^^^^

If you are working from a clone simply run::

  pip install -e .

Afterwards the ``pylocator`` command is available on your ``PATH``::

  pylocator /path/to/volume.nii.gz

Binary packages
---------------

The historical Debian packages for the GTK version are no longer maintained.
Building native packages for the Qt port is on the roadmap; contributions and
packaging notes are welcome.
