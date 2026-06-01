"""
models/product.py
-----------------
OOP representation of a product record.
Product is the base class.
Watch and Coffret are subclasses with kind-specific validation.

A COFFRET is a set containing a watch and its presentation box.
The strap field encodes the watch strap type for Watches, or combo contents for Coffrets (e.g. MECH/LEATH, BRCLT/JEW).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.cleaning.abbreviation_resolver import AbbreviationResolver


VALID_KINDS = {"WATCH", "COFFRET"}
VALID_GENDERS = {"LADIES", "GENTS", "UNISEX"}
VALID_MOVEMENTS = {"QUARTZ", "AUTOMATIC", "MECHANICAL"}


def _normalize_str(value: object) -> Optional[str]:
    """Strip whitespace and uppercase a string. Return None for empty/null."""
    if value is None:
        return None
    s = str(value).strip().upper()
    return s if s else None


def _is_zero_placeholder(value: object) -> bool:
    """Detect 0 / 0.0 used as NULL placeholder in missing_info.xlsx."""
    try:
        return float(value) == 0.0  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


@dataclass
class Product:
    """
    Base class for all Pierre Lannier products.
    Holds validated, normalized field values ready for DB insertion.
    """

    reference: str
    kind: str
    collection: str
    gender: str
    movement: str
    dial: Optional[str] = None
    strap: Optional[str] = None
    color: Optional[str] = None
    case_size: Optional[str] = None
    date_of_creation: Optional[date] = None
    date_of_reception: Optional[date] = None

    _is_partial: bool = field(default=False, repr=False, compare=False)
    _unknown_abbrevs: list[dict] = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.reference:
            raise ValueError("reference cannot be empty")
        if self.kind not in VALID_KINDS:
            raise ValueError(f"Invalid kind '{self.kind}'. Must be one of {VALID_KINDS}")
        if not self.collection:
            raise ValueError("collection cannot be empty")
        if self.gender not in VALID_GENDERS:
            raise ValueError(f"Invalid gender '{self.gender}'. Must be one of {VALID_GENDERS}")
        if self.movement not in VALID_MOVEMENTS:
            raise ValueError(
                f"Invalid movement '{self.movement}'. Must be one of {VALID_MOVEMENTS}"
            )

    @classmethod
    def from_row(
        cls,
        row: dict,
        resolver: Optional["AbbreviationResolver"] = None,
    ) -> "Product":
        """
        Build and return the correct Product subclass from a raw row dict.
        Keys must already be normalized to snake_case lowercase.
        """
        from src.cleaning.abbreviation_resolver import AbbreviationResolver

        if resolver is None:
            resolver = AbbreviationResolver()

        ref = _normalize_str(row.get("reference"))
        kind_raw = _normalize_str(row.get("kind")) or ""
        collection = _normalize_str(row.get("collection"))
        gender = _normalize_str(row.get("gender"))
        movement = _normalize_str(row.get("movement")) or ""

        movement_resolved = resolver.resolve_token(movement, "movement")
        movement = movement_resolved or movement
        movement_map = {
            "QUARTZ": "QUARTZ",
            "AUTOMATIC": "AUTOMATIC",
            "MECHANICAL": "MECHANICAL",
        }
        movement = movement_map.get(movement, movement)

        def opt(key: str) -> Optional[str]:
            val = row.get(key)
            if val is None or _is_zero_placeholder(val):
                return None
            return _normalize_str(val)

        dial = opt("dial")
        strap_raw = opt("bracelet")  # Note: input column is still "bracelet", but we rename to "strap"
        color_raw = opt("color")
        case_size = opt("case_size")

        strap, br_unknown = resolver.expand(strap_raw, "bracelet")  # resolver still uses "bracelet" category
        color, col_unknown = resolver.expand(color_raw, "color")
        unknown_abbrevs = [
            *[{"token": t, "field": "strap", "field_category": "bracelet"} for t in br_unknown],
            *[{"token": t, "field": "color", "field_category": "color"} for t in col_unknown],
        ]

        is_partial = any(f is None for f in [dial, strap, color, case_size])

        kwargs = dict(
            reference=ref,
            kind=kind_raw,
            collection=collection,
            gender=gender,
            movement=movement,
            dial=dial,
            strap=strap,
            color=color,
            case_size=str(case_size) if case_size else None,
            date_of_creation=row.get("date_of_creation"),
            date_of_reception=row.get("date_of_reception"),
        )

        if kind_raw not in VALID_KINDS:
            raise ValueError(f"Invalid kind '{kind_raw}'. Must be one of {VALID_KINDS}")

        if kind_raw == "COFFRET":
            obj: Product = Coffret(**kwargs)
        else:
            obj = Watch(**kwargs)

        obj._is_partial = is_partial
        obj._unknown_abbrevs = unknown_abbrevs
        return obj

    def to_db_dict(self) -> dict:
        return {
            "reference": self.reference,
            "kind": self.kind,
            "collection": self.collection,
            "gender": self.gender,
            "movement": self.movement,
            "dial": self.dial,
            "bracelet": self.strap,  # Map strap to database column "bracelet"
            "color": self.color,
            "case_size": self.case_size,
            "date_of_creation": self.date_of_creation,
            "date_of_reception": self.date_of_reception,
        }

    def __repr__(self) -> str:
        partial = " [PARTIAL]" if self._is_partial else ""
        return (
            f"{self.__class__.__name__}("
            f"ref={self.reference!r}, "
            f"kind={self.kind!r}, "
            f"collection={self.collection!r}, "
            f"gender={self.gender!r}{partial})"
        )


class Watch(Product):
    """A standard Pierre Lannier watch."""

    def __post_init__(self) -> None:
        self.kind = "WATCH"
        super().__post_init__()


class Coffret(Product):
    """
    A Pierre Lannier coffret set (watch + presentation box).
    The strap field encodes combo contents (e.g. MECH/LEATH, BRCLT/JEW).
    """

    def __post_init__(self) -> None:
        self.kind = "COFFRET"
        super().__post_init__()

    def combo_contents(self) -> list[str]:
        if not self.strap:
            return []
        return [p.strip() for p in self.strap.split("/")]
