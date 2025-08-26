# 🟣────────────────────────────────────────────
#       💜 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# ─────────────────────────────────────────────

from utils.cache.market_alert_cache import load_market_alert_cache, market_alert_cache
from utils.cache.mr_weakness_cache import (
    load_mr_weakness_user_cache,
    mr_weakness_user_cache,
)
from utils.loggers.espeon_log import espeon_log, EspeonContext


# 🐾────────────────────────────────────────────
#     💜 Load Everything in One Go
# 🐾────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader in order and logs once at the end.
    """

    # 🌸 Load Market Alerts into memory
    await load_market_alert_cache(bot)

    # 🌟 Load Mr. Weakness user settings into memory
    await load_mr_weakness_user_cache(bot)

    # 🎀 Unified single-line log
    espeon_log(
        tag="",
        label="🦋 CENTRAL CACHE",
        message=f"All caches refreshed and loaded (Market Alerts: {len(market_alert_cache)} + MR Weakness: {len(mr_weakness_user_cache)})",
        context=EspeonContext.STRAYMONS,
    )
