"""Common utility interfaces for the GPU validation platform."""

from __future__ import annotations

from typing import TypeVar


T = TypeVar("T")


def not_implemented(value: T) -> T:
    """Reserve a typed utility extension point for future shared helpers.

    Args:
        value: Placeholder value for the Phase 1 interface.

    Returns:
        The placeholder value unchanged once this interface is implemented.
    """
    # TODO: Replace this placeholder with a concrete shared utility.
    pass

