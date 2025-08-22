# 🟣────────────────────────────────────────────
#       💜 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# ─────────────────────────────────────────────

from utils.cache.market_alert_cache import load_market_alert_cache
from utils.cache.mr_weakness_cache import load_mr_weakness_user_cache
from utils.loggers.espeon_log import espeon_log, EspeonContext


# 🐾────────────────────────────────────────────
#     💜 Load Everything in One Go
# 🐾────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader in order and logs each step.
    """

    # 🌸 Load Market Alerts into memory
    await load_market_alert_cache(bot)
    espeon_log(
        "ready",
        "✅ Market alert cache loaded 🌸",
        context=EspeonContext.STRAYMONS,
    )

    # 🌟 Load Mr. Weakness user settings into memory
    await load_mr_weakness_user_cache(bot)
    espeon_log(
        "ready",
        "✅ Mr. Weakness user cache loaded 🌟",
        context=EspeonContext.STRAYMONS,
    )

    # 🎀 All caches done
    espeon_log(
        "ready",
        "🎀 All caches refreshed successfully! 💜",
        context=EspeonContext.STRAYMONS,
    )
