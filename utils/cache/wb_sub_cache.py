import json

from utils.group_func.wb_sub.wb_sub_db_func import fetch_all_wb_pings
from utils.loggers.espeon_log import espeon_log, EspeonContext

# 💜────────────────────────────────────────────
#       🟣 WB Ping Cache Loader
# 💜────────────────────────────────────────────

WB_PING_CACHE: dict[int, dict[str, dict]] = {}
# Structure:
# {
#   user_id: {
#       boss_name: {
#           "user_id": ..,
#           "user_name": ..,
#           "variant": ..,
#           "boss_name": ..,
#           "mode": ..,
#           "channel_id": ..,
#           "created_at": ..
#       },
#       ...
#   },
#   ...
# }


# 💜────────────────────────────────────────────
#   🟣 WB Ping Cache (Single Source of Truth)
# 💜────────────────────────────────────────────
import json
from utils.loggers.espeon_log import espeon_log, EspeonContext


async def load_wb_ping_cache(bot):
    """Replace WB_PING_CACHE entirely with given rows (fresh from DB)."""
    WB_PING_CACHE.clear()

    rows = await fetch_all_wb_pings(bot)
    for row in rows:
        user_id = row["user_id"]
        boss = row["boss_name"].lower()
        WB_PING_CACHE.setdefault(user_id, {})[boss] = row

    espeon_log(
        tag="db",
        message=f"🟣 WB Ping Cache rebuilt: {len(rows)} subs across {len(WB_PING_CACHE)} users",
        label="📡 WB PING CACHE",
        context=EspeonContext.STRAYMONS,
    )

    return WB_PING_CACHE


# 💜────────────────────────────────────────────
#       🟣 WB Ping Cache Fetchers
# 💜────────────────────────────────────────────


def wb_cache_fetch_user(user_id: int) -> dict[str, dict] | None:
    """Fetch all WB pings for a given user from cache."""
    return WB_PING_CACHE.get(user_id)


def wb_cache_fetch_user_boss(user_id: int, boss_name: str) -> dict | None:
    """Fetch a single WB ping row for a user by boss_name."""
    return WB_PING_CACHE.get(user_id, {}).get(boss_name.lower())


def wb_cache_fetch_user_boss_variant(
    user_id: int, boss_name: str, variant: str
) -> dict | None:
    """Fetch a single WB ping row for a user by boss_name + variant."""
    row = WB_PING_CACHE.get(user_id, {}).get(boss_name.lower())
    if row and row.get("variant") == variant.lower():
        return row
    return None


def wb_cache_fetch_all_boss(boss_name: str) -> list[dict]:
    """Fetch all WB pings for a given boss_name across all users."""
    boss_key = boss_name.lower()
    results = []
    for user_rows in WB_PING_CACHE.values():
        if boss_key in user_rows:
            results.append(user_rows[boss_key])
    return results


def wb_cache_fetch_all_boss_variant(boss_name: str, variant: str) -> list[dict]:
    """Fetch all WB pings for a given boss_name + variant across all users."""
    boss_key = boss_name.lower()
    variant_key = variant.lower()
    results = []
    for user_rows in WB_PING_CACHE.values():
        row = user_rows.get(boss_key)
        if row and row.get("variant") == variant_key:
            results.append(row)
    return results


# 💜────────────────────────────────────────────
#       🟣 WB Ping Cache Mutators
# 💜────────────────────────────────────────────


def wb_cache_upsert(row: dict) -> None:
    """Insert or replace a WB ping row in cache."""
    user_id = row["user_id"]
    boss = row["boss_name"].lower()
    WB_PING_CACHE.setdefault(user_id, {})[boss] = row


def wb_cache_update_variant_mode(
    user_id: int, boss_name: str, new_variant: str, new_mode: str
) -> bool:
    """Update only the variant + mode of an existing cache row."""
    boss_key = boss_name.lower()
    user_rows = WB_PING_CACHE.get(user_id)
    if not user_rows or boss_key not in user_rows:
        return False

    user_rows[boss_key]["variant"] = new_variant.lower()
    user_rows[boss_key]["mode"] = new_mode.lower()
    return True


def wb_cache_remove(user_id: int, boss_name: str) -> bool:
    """Remove a WB ping row from cache for a specific user+boss."""
    boss_key = boss_name.lower()
    user_rows = WB_PING_CACHE.get(user_id)
    if not user_rows or boss_key not in user_rows:
        return False

    del user_rows[boss_key]
    if not user_rows:
        WB_PING_CACHE.pop(user_id, None)
    return True


def wb_cache_remove_all(user_id: int) -> bool:
    """Remove all WB pings for a user from cache."""
    return WB_PING_CACHE.pop(user_id, None) is not None
