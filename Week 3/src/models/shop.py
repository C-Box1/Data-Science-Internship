"""
models/shop.py
--------------
OOP representation of a shop (point of sale) record.
Built from the column header strings in the Sales Per POS sheets.

Header format:
    '1113 - Kingdom Mall - Riyadh - AlHomaidhi - مركز المملكة - الرياض - الحميضي'
    '0001 - Main Store - مركز الرئيسي'
    '0002 - Transit Store - مكتب الشحن'
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional


# Known internal shop IDs — no city, no distributor
INTERNAL_SHOP_IDS = {"0001", "0002"}
ONLINE_SHOP_IDS   = {"0006"}

# Map of known shop_ids to their type
SHOP_TYPE_OVERRIDES: dict[str, str] = {
    "0001": "warehouse",
    "0002": "warehouse",
    "0006": "online",
}


@dataclass
class Shop:
    """
    Represents one point of sale.
    All fields come from the monthly report column headers.
    """

    shop_id:     str
    mall_name:   str
    city:        Optional[str]
    country:     str
    distributor: Optional[str]
    shop_type:   str  # 'retail' | 'warehouse' | 'online'

    def __post_init__(self) -> None:
        if not self.shop_id:
            raise ValueError("shop_id cannot be empty")
        if not self.mall_name:
            raise ValueError("mall_name cannot be empty")

    # ------------------------------------------------------------------
    # Factory method — parse from header string
    # ------------------------------------------------------------------

    @classmethod
    def from_header(cls, header: str, country: str = "Saudi Arabia") -> Optional["Shop"]:
        """
        Parse a shop from a column header string.
        Returns None if the string does not look like a valid shop header.

        Handles formats:
            '1113 - Kingdom Mall - Riyadh - AlHomaidhi - مركز المملكة ...'
            '0001 - Main Store - مركز الرئيسي'
            '0002 - Transit Store - مكتب الشحن'
        """
        if not header or not isinstance(header, str):
            return None

        header = header.strip()

        # Must start with a 4-digit ID
        if not re.match(r"^\d{4}", header):
            return None

        # Split on ' - ' but be careful: some mall names contain ' -' without space
        # Strategy: split on ' - ' and take first 4 meaningful Latin parts
        # Arabic parts (after first Arabic character) are ignored
        parts = header.split(" - ")

        # Filter out purely Arabic parts
        latin_parts = []
        for p in parts:
            stripped = p.strip()
            # Keep only if it has at least one ASCII character
            if any(ord(c) < 128 for c in stripped):
                latin_parts.append(stripped)
            else:
                break  # stop at first purely Arabic segment

        if not latin_parts:
            return None

        shop_id   = latin_parts[0].strip() if len(latin_parts) > 0 else None
        mall_name = latin_parts[1].strip() if len(latin_parts) > 1 else shop_id
        city      = latin_parts[2].strip() if len(latin_parts) > 2 else None
        distributor = latin_parts[3].strip() if len(latin_parts) > 3 else None

        if not shop_id:
            return None

        # Determine shop type
        shop_type = SHOP_TYPE_OVERRIDES.get(shop_id, "retail")

        # Internal/online shops have no city or distributor
        if shop_id in INTERNAL_SHOP_IDS or shop_id in ONLINE_SHOP_IDS:
            city = None
            distributor = None

        return cls(
            shop_id=shop_id,
            mall_name=mall_name,
            city=city,
            country=country,
            distributor=distributor,
            shop_type=shop_type,
        )

    # ------------------------------------------------------------------
    # DB serialization
    # ------------------------------------------------------------------

    def to_db_dict(self) -> dict:
        """Return a dict matching the market_information column names."""
        return {
            "shop_id":     self.shop_id,
            "mall_name":   self.mall_name,
            "city":        self.city,
            "country":     self.country,
            "distributor": self.distributor,
            "shop_type":   self.shop_type,
        }

    def __repr__(self) -> str:
        return (
            f"Shop(id={self.shop_id!r}, "
            f"name={self.mall_name!r}, "
            f"city={self.city!r}, "
            f"type={self.shop_type!r})"
        )