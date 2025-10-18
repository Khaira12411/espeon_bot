# 💜────────────────────────────────────────────
#       🟣 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# 💜────────────────────────────────────────────

from utils.cache.afk_user_cache import load_afk_cache
from utils.cache.cache_list import (
    AFK_CACHE,
    WB_PING_CACHE,
    ev_tracker_cache,
    market_alert_cache,
    mr_weakness_user_cache,
)
from utils.cache.ev_tracker_cache import load_ev_tracker_cache
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.cache.mr_weakness_cache import load_mr_weakness_user_cache
from utils.cache.wb_sub_cache import load_wb_ping_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 💜────────────────────────────────────────────
#     🟣 Load Everything in One Go
# 💜────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader and logs memory summary.
    """
    try:
        # 🌸 Load Market Alerts
        await load_market_alert_cache(bot)

        # 🌟 Load Mr. Weakness
        await load_mr_weakness_user_cache(bot)

        # 🔹 Load EV Tracker
        await load_ev_tracker_cache(bot)

        # 🟣 Load WB Ping Cache
        await load_wb_ping_cache(bot)

        # 🟣 Load AFK Users Cache
        await load_afk_cache(bot)

        # 🎀 Unified summary log
        espeon_log(
            tag="",
            label="🦋 CENTRAL CACHE",
            message=(
                f"All caches refreshed and loaded "
                f"(Market Alerts: {len(market_alert_cache)} ~{get_deep_size(market_alert_cache)//1024} KB + "
                f"MR Weakness: {len(mr_weakness_user_cache)} ~{get_deep_size(mr_weakness_user_cache)//1024} KB + "
                f"EV Trackers: {len(ev_tracker_cache)} ~{get_deep_size(ev_tracker_cache)//1024} KB + "
                f"WB Pings: {len(WB_PING_CACHE)} ~{get_deep_size(WB_PING_CACHE)//1024} KB + "
                f"AFK Users: {len(AFK_CACHE)} ~{get_deep_size(AFK_CACHE)//1024} KB)"
            ),
            context=EspeonContext.STRAYMONS,
        )
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to load all caches: {e}",
            context=EspeonContext.STRAYMONS,
        )


# 💜────────────────────────────────────────────
#       🟣 Combined Cache Fetcher 💜
# 💜────────────────────────────────────────────
async def fetch_all_caches_from_db(bot):
    """
    Fetch all active Market Alerts, Mr. Weakness settings, tracked EVs,
    WB Pings, and AFK Users in one DB call/transaction.
    Returns a dict with keys:
      - market_alerts
      - mr_weakness
      - ev_tracker
      - wb_pings
      - afk_users
    """
    results = {
        "market_alerts": [],
        "mr_weakness": [],
        "ev_tracker": [],
        "wb_pings": [],
        "afk_users": [],
    }

    try:
        async with bot.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 📌 Market Alerts
                ma_rows = await conn.fetch(
                    """
                    SELECT user_id, pokemon, dex_number, max_price, channel_id, role_id, notify
                    FROM market_alerts
                    WHERE notify = TRUE
                    """
                )
                results["market_alerts"] = [dict(r) for r in ma_rows]

                # 📌 Mr. Weakness
                mw_rows = await conn.fetch(
                    "SELECT user_id, display_type FROM mr_user_weakness_settings"
                )
                results["mr_weakness"] = [dict(r) for r in mw_rows]

                # 📌 EV Tracker
                ev_rows = await conn.fetch(
                    """
                    SELECT user_id, user_name, pokemon, dex_number,
                           hp, atk, spa, def, spd, spe,
                           hp_goal, atk_goal, spa_goal, def_goal, spd_goal, spe_goal
                    FROM ev_tracker
                    """
                )
                results["ev_tracker"] = [dict(r) for r in ev_rows]

                # 📌 WB Pings
                wb_rows = await conn.fetch(
                    "SELECT * FROM user_wb_ping ORDER BY created_at DESC"
                )
                results["wb_pings"] = [dict(r) for r in wb_rows]

                # 📌 AFK Users
                afk_rows = await conn.fetch(
                    "SELECT user_id, user_name, reason, started_at FROM afk_status"
                )
                results["afk_users"] = [dict(r) for r in afk_rows]

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to fetch all caches in one go: {e}",
            context=EspeonContext.STRAYMONS,
        )

    return results


# 💜────────────────────────────────────────────
#       🟣 Memory Size Helper 💜
# 💜────────────────────────────────────────────
import sys


def get_deep_size(obj, seen=None):
    """
    Recursively calculate approximate memory size of an object in bytes.
    """
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(
            get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items()
        )
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_deep_size(i, seen) for i in obj)

    return size
