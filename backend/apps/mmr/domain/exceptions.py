from __future__ import annotations


class StepNotFoundError(ValueError):
    """Raised when a step key does not exist in a version's schema."""
