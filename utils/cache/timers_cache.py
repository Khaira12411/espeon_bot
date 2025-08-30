from utils.group_func.timer.timer_db_func import fetch_all_timers
from utils.loggers.espeon_log import EspeonContext, espeon_log

# 🟣────────────────────────────────────────────
#       💜 Timer Cache Loader 💜
# ─────────────────────────────────────────────

timer_cache = (
    {}
)  # user_id -> {"pokemon_setting": str, "fish_setting": str, "battle_setting": str}


async def load_timer_cache(bot):
    """
    Load all user timer settings into memory cache.
    Uses the fetch_all_timers DB function.
    """
    timer_cache.clear()

    rows = await fetch_all_timers(bot)
    for row in rows:
        timer_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "pokemon_setting": row.get("pokemon_setting"),
            "fish_setting": row.get("fish_setting"),
            "battle_setting": row.get("battle_setting"),
        }

    # 🐟 Debug cache dump
    # print("[💜 DEBUG] Current timer_cache contents:")
    # for uid, data in timer_cache.items():
    #     print(f"  -> {uid}: {data}")

    espeon_log(
        tag="",
        label="⌚ TIMER CACHE",
        message=f"Loaded {len(timer_cache)} users' timer settings into cache",
        context=EspeonContext.STRAYMONS,
    )

    return timer_cache
