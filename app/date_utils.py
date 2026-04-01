"""Centralized date conversion for SQLite compatibility."""
from datetime import date


def to_date(val):
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str) and val:
        return date.fromisoformat(val)
    return None
