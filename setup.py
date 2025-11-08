#!/usr/bin/env python3

from pathlib import Path
from setuptools import find_packages, setup

PROJECT_ROOT = Path(__file__).parent.resolve()
README = (PROJECT_ROOT / "README").read_text(encoding="utf-8")

about: dict = {}
with open(PROJECT_ROOT / "pylocator" / "__init__.py", encoding="utf-8") as f:
    exec(f.read(), about)

setup(
    name="pylocator",
    version=about.get("__version__", "0.0.0"),
    description="Program for the localization of EEG-electrodes.",
    long_description=README,
    long_description_content_type="text/plain",
    author="Thorsten Kranz",
    author_email="thorstenkranz@gmail.com",
    url="http://pylocator.thorstenkranz.de",
    license="BSD-2-Clause",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.26",
        "nibabel>=5.2",
        "vtk>=9.3",
        "PySide6>=6.6",
    ],
    scripts=["bin/pylocator"],
)
