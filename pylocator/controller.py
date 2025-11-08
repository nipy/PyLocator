"""Qt controller that wires actions to the main window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from .nifti_loader import NiftiLoadError, load_nifti_volume
from .qt.main_window import MainWindow


class PyLocatorController:
    """Glue between the Qt widgets and back-end logic."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._main_window = MainWindow(parent)
        self._main_window.request_open_file.connect(self.select_and_load_volume)
        self._last_dir: Path | None = None

    # ------------------------------------------------------------------
    # Qt window helpers
    # ------------------------------------------------------------------
    def show(self) -> None:
        """Show the main window."""

        self._main_window.show()
        self._main_window.raise_()

    # ------------------------------------------------------------------
    # Volume loading
    # ------------------------------------------------------------------
    def select_and_load_volume(self) -> None:
        """Open a file dialog and load the chosen NIfTI volume."""

        start_dir = str(self._last_dir) if self._last_dir else str(Path.cwd())
        filename, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Open NIfTI volume",
            start_dir,
            "NIfTI files (*.nii *.nii.gz);;All files (*)",
        )
        if not filename:
            return
        self.load_volume(filename)

    def load_volume(self, filename: str) -> bool:
        """Load *filename* and display it in the VTK viewport."""

        try:
            volume = load_nifti_volume(filename)
        except NiftiLoadError as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(
                self._main_window,
                "Failed to load volume",
                str(exc),
            )
            return False

        self._last_dir = Path(filename).resolve().parent
        self._main_window.display_volume(volume)
        return True


__all__ = ["PyLocatorController"]
