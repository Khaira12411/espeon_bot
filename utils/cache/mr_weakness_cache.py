from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.group_func.mr_weakness.mr_weakness_db_func import (
    fetch_all_mr_user_settings,
)
from utils.cache.cache_list import mr_weakness_user_cache
# 🟣────────────────────────────────────────────
#       💜 MR Weakness User Cache Loader 💜
# ─────────────────────────────────────────────



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
        tag="",
        label="🌸 MR WEAKNESS CACHE",
        message=f"Loaded {len(mr_weakness_user_cache)} Mr. Weakness user settings into cache",
        context=EspeonContext.STRAYMONS,
    )

    return mr_weakness_user_cache

# 🟣────────────────────────────────────────────
#       💜 MR Weakness User Cache Helpers 💜
# ─────────────────────────────────────────────


def insert_mr_user(user_id: int, display_type: str):
    """Insert or update a user's Mr. Weakness display setting in cache."""
    mr_weakness_user_cache[user_id] = display_type
    espeon_log(
        tag="",
        label="🌸 MR WEAKNESS CACHE",
        message=f"Inserted/Updated user {user_id} with display_type '{display_type}' (cache now {len(mr_weakness_user_cache)} entries)",
        context=EspeonContext.STRAYMONS,
    )


def remove_mr_user(user_id: int):
    """Remove a user from the Mr. Weakness cache."""
    if user_id in mr_weakness_user_cache:
        mr_weakness_user_cache.pop(user_id)
        espeon_log(
            tag="",
            label="🌸 MR WEAKNESS CACHE",
            message=f"Removed user {user_id} from cache (cache now {len(mr_weakness_user_cache)} entries)",
            context=EspeonContext.STRAYMONS,
        )


def get_mr_user(user_id: int) -> str | None:
    """Get a user's display_type from the cache, or None if not set."""
    return mr_weakness_user_cache.get(user_id)


def update_mr_user(user_id: int, display_type: str):
    """
    Update an existing user's display_type in the cache.
    Does nothing if the user is not already in cache.
    """
    if user_id in mr_weakness_user_cache:
        old_display = mr_weakness_user_cache[user_id]
        mr_weakness_user_cache[user_id] = display_type
        espeon_log(
            tag="",
            label="🌸 MR WEAKNESS CACHE",
            message=f"Updated user {user_id} from '{old_display}' to '{display_type}'",
            context=EspeonContext.STRAYMONS,
        )
