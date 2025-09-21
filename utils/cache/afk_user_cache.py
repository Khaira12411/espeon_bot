import json
from utils.loggers.espeon_log import espeon_log, EspeonContext


# 💙────────────────────────────────────────────
#       🤍 AFK Cache Loader
# 💙────────────────────────────────────────────

AFK_CACHE: dict[int, dict] = {}
# Structure:
# {
#   user_id: {
#       "user_id": ..,
#       "user_name": ..,
#       "reason": ..,
#       "started_at": ..
#   },
#   ...
# }


# 💙────────────────────────────────────────────
#   🤍 AFK Cache (Single Source of Truth)
# 💙────────────────────────────────────────────

async def load_afk_cache(bot):
    """Replace AFK_CACHE entirely with rows (fresh from DB)."""
    from utils.group_func.afk.afk_db_func import fetch_all_afk

    AFK_CACHE.clear()

    rows = await fetch_all_afk(bot)
    for row in rows:
        AFK_CACHE[row["user_id"]] = row

    espeon_log(
        tag="db",
        message=f"[💙 AFK] Cache rebuilt: {len(rows)} entries",
        label="🌙 AFK CACHE",
        context=EspeonContext.STRAYMONS,
    )

    return AFK_CACHE


# 💙────────────────────────────────────────────
#       🤍 AFK Cache Fetchers
# 💙────────────────────────────────────────────
def afk_cache_fetch_user(user_id: int) -> dict | None:
    """Fetch AFK row for a specific user from cache."""
    return AFK_CACHE.get(user_id)


def afk_cache_fetch_all() -> list[dict]:
    """Fetch all AFK rows from cache."""
    return list(AFK_CACHE.values())


# 💙────────────────────────────────────────────
#       🤍 AFK Cache Mutators
# 💙────────────────────────────────────────────
def afk_cache_upsert(row: dict) -> None:
    """Insert or replace AFK row in cache."""
    AFK_CACHE[row["user_id"]] = row


def afk_cache_update_reason(user_id: int, new_reason: str | None) -> bool:
    """Update only the AFK reason of an existing cache row."""
    row = AFK_CACHE.get(user_id)
    if not row:
        return False
    row["reason"] = new_reason
    return True


def afk_cache_remove(user_id: int) -> bool:
    """Remove AFK row from cache for a specific user."""
    return AFK_CACHE.pop(user_id, None) is not None
