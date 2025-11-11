"""High level application helpers for PyLocator's Qt port."""

from __future__ import annotations

import vtk
vtk.vtkObject.GlobalWarningDisplayOff()
from PySide6.QtWidgets import QApplication
try:
    from .controller import PyLocatorController
except ImportError:
    from pylocator.controller import PyLocatorController


def _get_application() -> tuple[QApplication, bool]:
    """Return the active :class:`QApplication` and ownership flag."""

    existing = QApplication.instance()
    if existing is not None:
        return existing, False

    app = QApplication(sys.argv)
    app.setApplicationName("PyLocator")
    app.setOrganizationName("PyLocator Project")
    return app, True


def run_app(initial_volume: str | None = None) -> int:
    """Start the Qt application and block until it exits."""

    app, owns_app = _get_application()
    controller = PyLocatorController(parent=None)

    if initial_volume:
        controller.load_volume(initial_volume)

    controller.show()

    if owns_app:
        return app.exec()

    # When the caller already owns the QApplication we mimic exec()'s
    # behaviour by running the event loop until the main window is closed.
    # ``exec()`` is not re-entrant, therefore we simply return ``0``.
    return 0


__all__ = ["run_app"]

# --- Entry point for running as a script ---
if __name__ == "__main__":
    import sys
    sys.exit(run_app())
