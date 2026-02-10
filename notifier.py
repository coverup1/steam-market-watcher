"""Discord webhook notification module."""

from __future__ import annotations

import logging

import requests

LOGGER = logging.getLogger(__name__)


class DiscordNotifier:
    """Send markdown-formatted alerts to a Discord webhook."""

    def __init__(self, webhook_url: str, timeout: int = 10) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send_price_alert(
        self,
        skin_name: str,
        current_price: float,
        average_price: float,
        market_link: str,
        discount_pct: float,
    ) -> bool:
        message = (
            "🚨 **Steam Market Fırsat Alarmı**\n"
            f"**Skin:** {skin_name}\n"
            f"**Anlık Düşük Fiyat:** ${current_price:.2f}\n"
            f"**24s Ortalama Fiyat:** ${average_price:.2f}\n"
            f"**İndirim:** %{discount_pct:.2f}\n"
            f"**Link:** {market_link}"
        )

        payload = {"content": message}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
            if response.status_code in (200, 204):
                LOGGER.info("Discord notification sent for %s", skin_name)
                return True

            LOGGER.warning(
                "Discord notification failed for %s. status=%s body=%s",
                skin_name,
                response.status_code,
                response.text,
            )
            return False
        except requests.RequestException as exc:
            LOGGER.exception("Discord request failed for %s: %s", skin_name, exc)
            return False
