from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.group_func.mr_weakness.mr_weakness_db_func import (
    fetch_all_mr_user_settings,
)

# 🟣────────────────────────────────────────────
#       💜 MR Weakness User Cache Loader 💜
# ─────────────────────────────────────────────

mr_weakness_user_cache = {}  # user_id -> display_type


async def load_mr_weakness_user_cache(bot):
    """
    Load all Mr. Weakness user display settings into cache.
    Uses the fetch_all_mr_user_settings DB function.
    """
    mr_weakness_user_cache.clear()

    user_settings = await fetch_all_mr_user_settings(bot)
    for row in user_settings:
        mr_weakness_user_cache[row["user_id"]] = row["display_type"]

    espeon_log(
        "ready",
        f"Loaded {len(mr_weakness_user_cache)} Mr. Weakness user settings into cache",
        context=EspeonContext.STRAYMONS,
    )

    return mr_weakness_user_cache
