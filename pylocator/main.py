"""Application entry points for PyLocator."""

from __future__ import annotations

from .app import run_app


def run_pylocator(filename: str | None = None, surface: str | None = None) -> int:
    """Launch the Qt-based PyLocator application.

    Parameters
    ----------
    filename:
        Optional path to a NIfTI file that should be loaded during start-up.
    surface:
        Deprecated argument kept for backward compatibility. Surfaces are not
        yet supported in the Qt port and the value is ignored.

    Returns
    -------
    int
        The Qt application's exit code.
    """

    # ``surface`` is accepted to keep command-line compatibility with the
    # legacy GTK application. The modern Qt interface does not yet expose
    # surface loading, therefore the argument is intentionally unused.
    _ = surface
    return run_app(initial_volume=filename)


__all__ = ["run_pylocator"]


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(run_pylocator())
