"""Price analysis helpers for Steam Market watcher."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def calculate_weighted_average_last_24h(price_history: list[list[Any]]) -> float | None:
    """Calculate weighted average price for the last 24 hours.

    If there are no data points in the last 24 hours, falls back to all available data.
    Expects entries: [timestamp_string, price_string, volume_string]
    """
    if not price_history:
        return None

    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=24)

    last_24h_points: list[tuple[float, int]] = []
    all_points: list[tuple[float, int]] = []

    for row in price_history:
        if len(row) < 3:
            continue

        timestamp_raw, price_raw, volume_raw = row[0], row[1], row[2]

        price = _safe_float(price_raw)
        volume = _safe_int(volume_raw)
        timestamp = _parse_steam_timestamp(timestamp_raw)

        if price is None or volume is None or volume <= 0:
            continue

        all_points.append((price, volume))

        if timestamp and timestamp >= threshold:
            last_24h_points.append((price, volume))

    if last_24h_points:
        return _weighted_average(last_24h_points)

    if all_points:
        return _weighted_average(all_points)

    return None


def is_discount_significant(current_price: float, average_price: float, discount_threshold_pct: float = 10.0) -> bool:
    """Return True if current price is at least threshold percent below average."""
    if average_price <= 0:
        return False

    discount_pct = ((average_price - current_price) / average_price) * 100
    return discount_pct >= discount_threshold_pct


def discount_percentage(current_price: float, average_price: float) -> float:
    """Calculate discount percentage of current vs average price."""
    if average_price <= 0:
        return 0.0
    return ((average_price - current_price) / average_price) * 100


def _parse_steam_timestamp(timestamp_raw: Any) -> datetime | None:
    if not isinstance(timestamp_raw, str):
        return None

    normalized = timestamp_raw.replace(" +0", "")

    for fmt in ("%b %d %Y %H:", "%b %d %Y %H:%M"):
        try:
            parsed = datetime.strptime(normalized, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _weighted_average(points: list[tuple[float, int]]) -> float:
    total_price_volume = sum(price * volume for price, volume in points)
    total_volume = sum(volume for _, volume in points)
    return total_price_volume / total_volume
