#!/usr/bin/env python

from distutils.core import setup
import sys

import nipy_ui 


# For some commands, use setuptools
if len(set(('develop', 'sdist', 'release', 'bdist_egg', 'bdist_rpm',
           'bdist', 'bdist_dumb', 'bdist_wininst', 'install_egg_info',
           'build_sphinx', 'egg_info', 'easy_install',
            )).intersection(sys.argv)) > 0:
    from setupegg import extra_setuptools_args

# extra_setuptools_args is injected by the setupegg.py script, for
# running the setup with setuptools.
if not 'extra_setuptools_args' in globals():
    extra_setuptools_args = dict()


setup(name='pylocator',
      version=nipy_ui.__version__,
      summary='Program for the localization of EEG-electrodes.',
      author='Thorsten Kranz',
      author_email='thorstenkranz@gmail.com',
      url='http://...',
      description="""
Program for the localization of EEG-electrodes.
""",
      long_description=file('README').read(),
      license='BSD',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Education',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering',
          'Topic :: Utilities',
      ],
      platforms='any',
      #package_data={'nipy_ui.data': ['nipy_ui/data/*'],},
      packages=['pylocator', 'pylocator.test'],
      **extra_setuptools_args)

