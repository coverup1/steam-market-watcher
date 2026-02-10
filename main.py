"""Main entrypoint for Steam Community Market watcher."""

from __future__ import annotations

import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from analyzer import (
    calculate_weighted_average_last_24h,
    discount_percentage,
    is_discount_significant,
)
from notifier import DiscordNotifier
from steam_client import SteamClient

SKINS_TO_WATCH = [
    "AK-47 | Slate (Field-Tested)",
    "AWP | Atheris (Field-Tested)",
    "USP-S | Cortex (Field-Tested)",
    "Glock-18 | Vogue (Field-Tested)",
    "M4A1-S | Night Terror (Field-Tested)",
    "AK-47 | Elite Build (Field-Tested)",
    "AWP | Worm God (Field-Tested)",
    "M4A4 | Griffin (Field-Tested)",
    "USP-S | Flashback (Field-Tested)",
    "FAMAS | Mecha Industries (Field-Tested)",
]

DISCOUNT_THRESHOLD_PERCENT = 10.0
MIN_LOOP_SECONDS = 45
MAX_LOOP_SECONDS = 120
NOTIFICATION_COOLDOWN_MINUTES = 30

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def should_notify(last_notification_at: datetime | None, cooldown_minutes: int) -> bool:
    if last_notification_at is None:
        return True

    now = datetime.now(timezone.utc)
    return now - last_notification_at >= timedelta(minutes=cooldown_minutes)


def run() -> None:
    load_dotenv()
    configure_logging()

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL .env dosyasında tanımlı olmalı.")

    steam_client = SteamClient(currency=1, appid=730)
    notifier = DiscordNotifier(webhook_url=webhook_url)

    last_notified: dict[str, datetime] = {}

    LOGGER.info("Steam Market watcher started. Watching %d skins.", len(SKINS_TO_WATCH))

    while True:
        try:
            for skin in SKINS_TO_WATCH:
                LOGGER.info("Checking skin: %s", skin)

                price_history = steam_client.get_price_history(skin)
                average_price = calculate_weighted_average_last_24h(price_history)

                if average_price is None:
                    LOGGER.warning("No valid average price for %s, skipping.", skin)
                    continue

                current_lowest = steam_client.get_lowest_price(skin)
                if current_lowest is None:
                    LOGGER.warning("No current lowest price for %s, skipping.", skin)
                    continue

                if is_discount_significant(current_lowest, average_price, DISCOUNT_THRESHOLD_PERCENT):
                    discount_pct = discount_percentage(current_lowest, average_price)
                    if should_notify(last_notified.get(skin), NOTIFICATION_COOLDOWN_MINUTES):
                        market_link = steam_client.build_listing_url(skin)
                        sent = notifier.send_price_alert(
                            skin_name=skin,
                            current_price=current_lowest,
                            average_price=average_price,
                            market_link=market_link,
                            discount_pct=discount_pct,
                        )
                        if sent:
                            last_notified[skin] = datetime.now(timezone.utc)
                    else:
                        LOGGER.info("Cooldown active for %s, notification skipped.", skin)
                else:
                    LOGGER.info(
                        "No alert for %s (current=%.2f, avg=%.2f)",
                        skin,
                        current_lowest,
                        average_price,
                    )

                item_delay = random.uniform(2, 6)
                time.sleep(item_delay)

            sleep_seconds = random.randint(MIN_LOOP_SECONDS, MAX_LOOP_SECONDS)
            LOGGER.info("Loop completed. Sleeping for %d seconds.", sleep_seconds)
            time.sleep(sleep_seconds)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Unexpected error in main loop: %s", exc)
            recovery_sleep = random.randint(15, 30)
            LOGGER.info("Recovering after error. Sleeping for %d seconds.", recovery_sleep)
            time.sleep(recovery_sleep)


if __name__ == "__main__":
    run()
