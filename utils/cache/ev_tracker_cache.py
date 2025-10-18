from utils.group_func.ev_tracker.ev_tracker_db_func import fetch_all_tracked_evs
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.cache.cache_list import ev_tracker_cache
# 🟣────────────────────────────────────────────
#       💜 EV Tracker Cache System 💜
# ─────────────────────────────────────────────


# 🌸 1️⃣ Load everything on startup
async def load_ev_tracker_cache(bot):
    """Load all tracked EVs into memory cache (startup only)."""
    ev_tracker_cache.clear()
    rows = await fetch_all_tracked_evs(bot)
    for row in rows:
        insert_ev_tracker_cache(row)

    espeon_log(
        tag="",
        label="🐼 EV TRACKER CACHE",
        message=f"Loaded {len(ev_tracker_cache)} users' EVs into cache",
        context=EspeonContext.STRAYMONS,
    )
    return ev_tracker_cache


# 🌸 2️⃣ Insert or update one entry
def insert_ev_tracker_cache(row: dict):
    """Insert/update one user's EV tracker row into cache."""
    ev_tracker_cache[row["user_id"]] = {
        "user_name": row.get("user_name"),
        "pokemon": row["pokemon"],
        "dex_number": row.get("dex_number"),
        "evs": {
            stat: row[stat]
            for stat in ["hp", "atk", "spa", "def", "spd", "spe"]
            if row.get(stat) is not None
        },
        "goals": {
            stat: row[f"{stat}_goal"]
            for stat in ["hp", "atk", "spa", "def", "spd", "spe"]
            if row.get(f"{stat}_goal") is not None
        },
    }


# 🌸 3️⃣ Remove one entry
def remove_ev_tracker_cache(user_id: int):
    """Remove a user from EV tracker cache."""
    ev_tracker_cache.pop(user_id, None)


# 🌸 4️⃣ Update a specific EV or goal
def update_ev_tracker_cache(
    user_id: int, field: str, value: int | None, is_goal: bool = False
):
    """Update a single EV stat or goal in cache without reload."""
    if user_id not in ev_tracker_cache:
        return
    key = "goals" if is_goal else "evs"
    ev_tracker_cache[user_id][key][field] = value


# 🌸 5️⃣ Safe getter
def get_ev_tracker(user_id: int) -> dict | None:
    """Safely fetch a user's EV tracker data from cache."""
    return ev_tracker_cache.get(user_id)


# 🌸 6️⃣ Safe getter (all users)
def get_all_ev_trackers() -> dict[int, dict]:
    """Return a shallow copy of the entire EV tracker cache."""
    return ev_tracker_cache.copy()
