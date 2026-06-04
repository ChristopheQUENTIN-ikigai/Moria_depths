"""
Entity — a lightweight integer-ID wrapper.

Entities own no data; they are just identifiers used to look up
components in the World registry.
"""
from __future__ import annotations


class Entity:
    """Thin wrapper around an int ID for readability and hashing."""

    __slots__ = ("id",)

    def __init__(self, eid: int) -> None:
        self.id = eid

    def __int__(self) -> int:
        return self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entity):
            return self.id == other.id
        if isinstance(other, int):
            return self.id == other
        return NotImplemented

    def __repr__(self) -> str:
        return f"Entity({self.id})"
