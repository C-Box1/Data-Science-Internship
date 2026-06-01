"""
models/abbreviation.py
----------------------
Represents one row in the abbreviations table.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Abbreviation:
    abbreviation: str
    full_term: str
    field_category: str
    abbrev_id: int | None = None

    def to_db_dict(self) -> dict:
        return {
            "abbreviation": self.abbreviation.upper(),
            "full_term": self.full_term.upper(),
            "field_category": self.field_category.lower(),
        }
