"""
cleaning/abbreviation_resolver.py
---------------------------------
Expands abbreviations using the abbreviations database table.

Lookup is case-insensitive: brclt, BRCLT, and Brclt all resolve the same way.
Combo values like MECH/LEATH expand each slash-separated part independently.
Unknown tokens are returned so the UI can ask the employee what they mean.
"""

from __future__ import annotations

from typing import Optional

from psycopg2.extensions import connection as PgConnection

from src.db import repository as repo

# Built-in defaults used when no database connection is available (tests).
DEFAULT_ALIASES: dict[str, dict[str, str]] = {
    "bracelet": {
        "BRCLT": "BRACELET",
        "BRACE": "BRACELET",
        "LEATH": "LEATHER STRAP",
        "MECH": "MESH",
        "JEW": "JEWELLERY STRAP",
    },
    "color": {
        "YG": "YELLOW GOLD",
        "RG": "ROSE GOLD",
        "PG": "PINK GOLD",
        "SS": "STAINLESS STEEL",
        "BK": "BLACK",
        "WH": "WHITE",
    },
    "movement": {
        "AUTO": "AUTOMATIC",
    },
}


class AbbreviationResolver:
    """Resolve abbreviations for product fields."""

    def __init__(
        self,
        conn: Optional[PgConnection] = None,
        alias_maps: Optional[dict[str, dict[str, str]]] = None,
    ) -> None:
        self._conn = conn
        if alias_maps is not None:
            self._maps = alias_maps
        elif conn is not None:
            self._maps = repo.load_abbreviation_maps(conn)
        else:
            self._maps = DEFAULT_ALIASES

    def reload(self) -> None:
        """Refresh maps from the database after new abbreviations are added."""
        if self._conn is not None:
            self._maps = repo.load_abbreviation_maps(self._conn)

    def expand(
        self,
        value: Optional[str],
        field_category: str,
    ) -> tuple[Optional[str], list[str]]:
        """
        Expand abbreviations in a field value.

        Returns:
            (expanded_value, unknown_tokens)
        """
        if value is None:
            return None, []

        alias_map = self._maps.get(field_category, {})
        parts = [p.strip() for p in str(value).split("/")]
        expanded: list[str] = []
        unknown: list[str] = []

        for part in parts:
            key = part.upper()
            if key in alias_map:
                expanded.append(alias_map[key])
            elif part.upper() == part and len(part) <= 6 and part.isalpha():
                # Short all-caps token that might be an unknown abbreviation
                unknown.append(part)
                expanded.append(part)
            else:
                expanded.append(part.upper())

        return "/".join(expanded), unknown

    def resolve_token(self, token: str, field_category: str) -> Optional[str]:
        """Case-insensitive single-token lookup."""
        return self._maps.get(field_category, {}).get(token.upper())

    def all_unknown_in_row(self, row: dict) -> list[dict]:
        """Scan bracelet/color fields and collect unknown abbreviation tokens."""
        findings: list[dict] = []
        for field, category in (("bracelet", "bracelet"), ("color", "color")):
            raw = row.get(field)
            if raw is None:
                continue
            _, unknown = self.expand(str(raw), category)
            for token in unknown:
                findings.append(
                    {
                        "token": token,
                        "field": field,
                        "field_category": category,
                        "context_value": str(raw),
                    }
                )
        return findings
