from utils.group_func.ev_tracker.ev_tracker_db_func import fetch_all_tracked_evs
from utils.loggers.espeon_log import EspeonContext, espeon_log

# 🟣────────────────────────────────────────────
#       💜 EV Tracker Cache Loader 💜
# ─────────────────────────────────────────────

ev_tracker_cache = (
    {}
)  # user_id -> {"user_name": str, "pokemon": str, "dex_number": int, "evs": dict, "goals": dict}


async def load_ev_tracker_cache(bot):
    """
    Load all tracked EVs into memory cache.
    Uses the fetch_all_tracked_evs DB function.
    """
    ev_tracker_cache.clear()

    rows = await fetch_all_tracked_evs(bot)
    for row in rows:
        ev_tracker_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "pokemon": row["pokemon"],
            "dex_number": row.get("dex_number"),
            "evs": {
                stat: row[stat]
                for stat in ["hp", "atk", "spa", "def", "spd", "spe"]
                if row[stat] is not None
            },
            "goals": {
                stat: row[f"{stat}_goal"]
                for stat in ["hp", "atk", "spa", "def", "spd", "spe"]
                if row.get(f"{stat}_goal") is not None
            },
        }

    # 💜 Debug cache dump
    # print("[💜 DEBUG] Current ev_tracker_cache contents:")
    # for uid, data in ev_tracker_cache.items():
    # print(f"  -> {uid}: {data}")

    espeon_log(
        tag="",
        label="🐼 EV TRACKER CACHE",
        message=f"Loaded {len(ev_tracker_cache)} users' EVs into cache",
        context=EspeonContext.STRAYMONS,
    )

    return ev_tracker_cache
