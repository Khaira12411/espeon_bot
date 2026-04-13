from utils.cache.cache_list import mr_weakness_user_cache, weakness_data_cache
from utils.group_func.mr_weakness.mr_weakness_db_func import fetch_all_mr_user_settings
from utils.loggers.espeon_log import EspeonContext, espeon_log

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
        mr_weakness_user_cache[row["user_id"]] = {
            "user_name": row.get("user_name", ""),
            "display_type": row["display_type"],
        }

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


def insert_mr_user(user_id: int, user_name: str, display_type: str):
    """Insert or update a user's Mr. Weakness settings in cache."""
    mr_weakness_user_cache[user_id] = {
        "user_name": user_name,
        "display_type": display_type,
    }
    espeon_log(
        tag="",
        label="🌸 MR WEAKNESS CACHE",
        message=f"Inserted/Updated user {user_id} ({user_name}) with display_type '{display_type}' (cache now {len(mr_weakness_user_cache)} entries)",
        context=EspeonContext.STRAYMONS,
    )


def remove_mr_user(user_id: int):
    """Remove a user from the Mr. Weakness cache."""
    if user_id in mr_weakness_user_cache:
        removed = mr_weakness_user_cache.pop(user_id)
        espeon_log(
            tag="",
            label="🌸 MR WEAKNESS CACHE",
            message=f"Removed user {user_id} ({removed['user_name']}) from cache (cache now {len(mr_weakness_user_cache)} entries)",
            context=EspeonContext.STRAYMONS,
        )


def get_mr_user(user_id: int) -> dict[str, str] | None:
    """Get a user's settings (user_name + display_type) from the cache, or None if not set."""
    return mr_weakness_user_cache.get(user_id)


def update_mr_user(
    user_id: int, user_name: str | None = None, display_type: str | None = None
):
    """
    Update an existing user's settings in the cache.
    Does nothing if the user is not already in cache.
    """
    if user_id in mr_weakness_user_cache:
        old_entry = mr_weakness_user_cache[user_id].copy()
        if user_name is not None:
            mr_weakness_user_cache[user_id]["user_name"] = user_name
        if display_type is not None:
            mr_weakness_user_cache[user_id]["display_type"] = display_type

        espeon_log(
            tag="",
            label="🌸 MR WEAKNESS CACHE",
            message=f"Updated user {user_id} from {old_entry} to {mr_weakness_user_cache[user_id]}",
            context=EspeonContext.STRAYMONS,
        )


def get_display_type_via_user_name(user_name: str) -> str | None:
    """Get a user's display_type from the cache using their user_name, or None if not found."""
    for user_id, data in mr_weakness_user_cache.items():
        if data["user_name"] == user_name:
            return data["display_type"]
    return None


def get_display_type_via_user_id(user_id: int) -> str | None:
    """Get a user's display_type from the cache using their user_id, or None if not found."""
    user_data = mr_weakness_user_cache.get(user_id)
    return user_data["display_type"] if user_data else None


def _normalize_pokemon_cache_key(pokemon_name: str) -> str:
    """Return a canonical key so cache lookups are case/space-insensitive."""
    return pokemon_name.strip().lower()


def upsert_weakness_data_cache(
    pokemon_name: str, title: str, description: str, note: str, footer: str, color
):
    """Insert or update weakness data for a Pokemon in the cache."""
    cache_key = _normalize_pokemon_cache_key(pokemon_name)
    weakness_data_cache[cache_key] = {
        "title": title,
        "description": description,
        "note": note,
        "footer": footer,
        "color": color,
    }
    espeon_log(
        tag="",
        label="🌸 WEAKNESS DATA CACHE",
        message=f"Upserted weakness data for '{pokemon_name}' into cache (cache now {len(weakness_data_cache)} entries)",
        context=EspeonContext.ESPEON,
    )


def get_weakness_data(pokemon_name: str) -> dict[str, str] | None:
    """Get weakness data for a Pokemon from the cache, or None if not found."""
    cache_key = _normalize_pokemon_cache_key(pokemon_name)
    return weakness_data_cache.get(cache_key)
