import discord
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.database.straymons_members_db import fetch_all_straymon_members
from utils.cache.cache_list import straymon_member_cache
# 💜────────────────────────────────────────────
#   🟣 Straymons Members Cache
# 💜────────────────────────────────────────────
async def load_straymon_members_cache(bot: discord.Client):
    """
    Load all Straymons members into the cache.
    """
    try:
        rows = await fetch_all_straymon_members(bot)
        for row in rows:
            user_id = row["user_id"]
            straymon_member_cache[user_id] = {
                "user_name": row["user_name"],
                "channel_id": row["channel_id"],
            }
        espeon_log(
            tag="cache",
            message=f"Loaded {len(straymon_member_cache)} straymons members into cache.",
            label="💠 STRAYMONS MEMBERS CACHE",
            context=EspeonContext.ESPEON,
        )
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"⚠️ Failed to load straymons members cache: {e}",
            exc=e,
            label="💠 STRAYMONS MEMBERS CACHE",
            context=EspeonContext.ESPEON,
        )

def fetch_straymon_member_id_by_name(user_name: str) -> int | None:
    """
    Fetch straymon member ID by user_name from cache.
    Returns user_id if found, else None.
    """
    for user_id, data in straymon_member_cache.items():
        if data["user_name"].lower() == user_name.lower():
            return user_id
    return None