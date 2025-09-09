# 🟣────────────────────────────────────────────
#       💜 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# ─────────────────────────────────────────────

from utils.cache.ev_tracker_cache import ev_tracker_cache, load_ev_tracker_cache
from utils.cache.market_alert_cache import load_market_alert_cache, market_alert_cache, _market_alert_index
from utils.cache.mr_weakness_cache import (
    load_mr_weakness_user_cache,
    mr_weakness_user_cache,
)
from utils.cache.timers_cache import load_timer_cache, timer_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 🐾────────────────────────────────────────────
#     💜 Load Everything in One Go
# 🐾────────────────────────────────────────────
async def old_load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader in order and logs once at the end.
    """

    # 🌸 Load Market Alerts into memory
    await load_market_alert_cache(bot)

    # 🌟 Load Mr. Weakness user settings into memory
    await load_mr_weakness_user_cache(bot)

    # 🐼 Load EV Tracker cache
    await load_ev_tracker_cache(bot)

    # 🎀 Unified single-line log
    espeon_log(
        tag="",
        label="🦋 CENTRAL CACHE",
        message=(
            f"All caches refreshed and loaded "
            f"(Market Alerts: {len(market_alert_cache)} + "
            f"MR Weakness: {len(mr_weakness_user_cache)} + "
            f"EV Trackers: {len(ev_tracker_cache)}"
        ),
        context=EspeonContext.STRAYMONS,
    )


async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Uses the combined fetcher to populate caches in memory.
    """
    # 🔹 Fetch all DB data in one go
    results = await fetch_all_caches_from_db(bot)

    # 🌸 Market Alerts
    market_alert_cache.clear()
    _market_alert_index.clear()  # reset index

    for alert in results.get("market_alerts", []):
        alert_entry = {
            "pokemon": alert["pokemon"].lower(),
            "dex_number": alert["dex_number"],
            "max_price": alert["max_price"],
            "channel_id": alert["channel_id"],
            "role_id": alert.get("role_id"),
            "notify": alert.get("notify", True),
            "user_id": alert.get("user_id"),
        }
        market_alert_cache.append(alert_entry)

        key = (
            alert_entry["pokemon"],
            alert_entry["channel_id"],
            alert_entry["user_id"],
        )
        _market_alert_index[key] = alert_entry

    """# 🪄 Debug log for Market Alerts cache + index
    espeon_log(
        "info",
        f"[Market Alert Cache] After load → {len(market_alert_cache)} in list, "
        f"{len(_market_alert_index)} in index "
        f"(sample keys: {list(_market_alert_index.keys())[:3]})",
        context=EspeonContext.STRAYMONS,
    )"""

    # 🌟 Mr. Weakness
    mr_weakness_user_cache.clear()
    for row in results.get("mr_weakness", []):
        mr_weakness_user_cache[row["user_id"]] = row["display_type"]

    # 🐼 EV Tracker
    ev_tracker_cache.clear()
    for row in results.get("ev_tracker", []):
        ev_tracker_cache[row["user_id"]] = row

    # 🎀 Log summary
    espeon_log(
        tag="",
        label="🦋 CENTRAL CACHE",
        message=(
            f"All caches refreshed and loaded "
            f"(Market Alerts: {len(market_alert_cache)} ~{get_deep_size(market_alert_cache)//1024} KB + "
            f"MR Weakness: {len(mr_weakness_user_cache)} ~{get_deep_size(mr_weakness_user_cache)//1024} KB + "
            f"EV Trackers: {len(ev_tracker_cache)} ~{get_deep_size(ev_tracker_cache)//1024} KB)"
        ),
        context=EspeonContext.STRAYMONS,
    )


# 🟣────────────────────────────────────────────
#       💜 Combined Cache Fetcher 💜
# ─────────────────────────────────────────────
async def fetch_all_caches_from_db(bot):
    """
    Fetch all active Market Alerts, Mr. Weakness settings, and tracked EVs
    in one DB call/transaction. Returns a dict with keys:
      - market_alerts
      - mr_weakness
      - ev_tracker
    """
    results = {
        "market_alerts": [],
        "mr_weakness": [],
        "ev_tracker": [],
    }

    try:
        async with bot.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 📌 1️⃣ Market Alerts
                ma_rows = await conn.fetch(
                    """
                    SELECT user_id, pokemon, dex_number, max_price, channel_id, role_id, notify
                    FROM market_alerts
                    WHERE notify = TRUE
                    """
                )
                results["market_alerts"] = [dict(r) for r in ma_rows]

                # 📌 2️⃣ Mr. Weakness
                mw_rows = await conn.fetch(
                    """
                    SELECT user_id, display_type
                    FROM mr_user_weakness_settings
                    """
                )
                results["mr_weakness"] = [dict(r) for r in mw_rows]

                # 📌 3️⃣ EV Tracker
                ev_rows = await conn.fetch(
                    """
                    SELECT user_id, user_name, pokemon, dex_number,
                           hp, atk, spa, def, spd, spe,
                           hp_goal, atk_goal, spa_goal, def_goal, spd_goal, spe_goal
                    FROM ev_tracker
                    """
                )
                results["ev_tracker"] = [dict(r) for r in ev_rows]

    except Exception as e:
        from utils.loggers.espeon_log import espeon_log, EspeonContext

        espeon_log(
            tag="error",
            message=f"Failed to fetch all caches in one go: {e}",
            context=EspeonContext.STRAYMONS,
        )

    return results
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
