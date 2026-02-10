"""Steam Community Market data client."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import requests

LOGGER = logging.getLogger(__name__)

MARKET_BASE_URL = "https://steamcommunity.com/market"
PRICE_HISTORY_ENDPOINT = f"{MARKET_BASE_URL}/pricehistory"
LISTINGS_ENDPOINT = f"{MARKET_BASE_URL}/listings/730"
PRICE_OVERVIEW_ENDPOINT = f"{MARKET_BASE_URL}/priceoverview"


class SteamClient:
    """Client for pulling market data from Steam Community Market."""

    def __init__(self, currency: int = 1, appid: int = 730, timeout: int = 15) -> None:
        self.currency = currency
        self.appid = appid
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )

    def get_price_history(self, market_hash_name: str) -> list[list[Any]]:
        """Fetch raw price history list for an item.

        Steam returns: [["May 18 2026 01: +0", "1.23", "5"], ...]
        """
        params = {
            "appid": self.appid,
            "market_hash_name": market_hash_name,
            "currency": self.currency,
        }
        try:
            response = self.session.get(PRICE_HISTORY_ENDPOINT, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("success"):
                LOGGER.warning("Steam price history returned unsuccessful for %s", market_hash_name)
                return []
            return payload.get("prices", [])
        except requests.RequestException as exc:
            LOGGER.exception("Price history request failed for %s: %s", market_hash_name, exc)
            return []
        except ValueError as exc:
            LOGGER.exception("Invalid JSON in price history response for %s: %s", market_hash_name, exc)
            return []

    def get_lowest_price(self, market_hash_name: str) -> float | None:
        """Fetch current lowest price from Steam priceoverview endpoint."""
        params = {
            "appid": self.appid,
            "market_hash_name": market_hash_name,
            "currency": self.currency,
        }
        try:
            response = self.session.get(PRICE_OVERVIEW_ENDPOINT, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("success"):
                LOGGER.warning("Steam price overview returned unsuccessful for %s", market_hash_name)
                return None

            raw_price = payload.get("lowest_price")
            return _parse_price(raw_price)
        except requests.RequestException as exc:
            LOGGER.exception("Lowest price request failed for %s: %s", market_hash_name, exc)
            return None
        except ValueError as exc:
            LOGGER.exception("Invalid JSON in price overview response for %s: %s", market_hash_name, exc)
            return None

    def build_listing_url(self, market_hash_name: str) -> str:
        """Build Steam market listing URL for the given item."""
        encoded = quote(market_hash_name, safe="")
        return f"{LISTINGS_ENDPOINT}/{encoded}"


def _parse_price(raw_price: str | None) -> float | None:
    """Parse Steam lowest_price value into float.

    Handles strings like "$1.23", "1,23€", "₺45,99".
    """
    if not raw_price:
        return None

    cleaned = raw_price.strip()
    allowed_chars = "0123456789,."
    cleaned = "".join(char for char in cleaned if char in allowed_chars)

    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        LOGGER.warning("Unable to parse price value: %s", raw_price)
        return None
