# 🟣────────────────────────────────────────────
#           💜 Market Alert Cache Loader 💜
# ─────────────────────────────────────────────

from utils.group_func.market_alert.db_func.market_alert_db_func import (
    fetch_active_market_alerts,
)
from utils.loggers.espeon_log import espeon_log, EspeonContext

# Global cache list
market_alert_cache = []


async def load_market_alert_cache(bot):
    """
    Load all active market alerts (notify = TRUE) into memory cache.
    Stored as a list of alert dicts for iteration.
    """
    # Clear the existing list instead of rebinding
    market_alert_cache.clear()

    active_alerts = await fetch_active_market_alerts(bot)

    for alert in active_alerts:
        # Ensure consistent keys: lowercase Pokémon name
        alert_entry = {
            "pokemon_name": alert["pokemon"].lower(),
            "dex_number": alert["dex_number"],
            "max_price": alert["max_price"],
            "channel_id": alert["channel_id"],
            "role_id": alert.get("role_id"),
            "notify": alert.get("notify", True),
        }
        market_alert_cache.append(alert_entry)

    # Log number of alerts loaded using espeon_log
    espeon_log(
        tag="",
        label="🦄 MARKET ALERT CACHE",
        message=f"Loaded {len(market_alert_cache)} market alerts into cache",
        context=EspeonContext.STRAYMONS,
    )

    return market_alert_cache
