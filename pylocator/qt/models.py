from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Marker:
    x: int
    y: int
    z: int


__all__ = ["Marker"]

