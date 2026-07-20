import discord
from typing import Any, Dict, Optional
from utils.cache.cache_list import clan_promo_item_cache
from utils.database.clan_promo_item_db import fetch_all_member_promo_items
from utils.loggers.espeon_log import EspeonContext, espeon_log

async def load_member_promo_item_cache(bot: discord.Client):
    """
    Load all member promo items from the database into the cache.
    """
    try:
        member_promo_items = await fetch_all_member_promo_items(bot)
        clan_promo_item_cache.clear()
        for item in member_promo_items:
            key = (item["promo_name"], item["user_id"])
            clan_promo_item_cache[key] = item
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to load member promo item cache: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return None

def upsert_member_promo_item_cache(
    promo_name: str,
    user_id: int,
    user_name: str,
    drops: int,
):
    """
    Upsert a member's promo item into the cache.
    """
    key = (promo_name, user_id)
    clan_promo_item_cache[key] = {
        "promo_name": promo_name,
        "user_id": user_id,
        "user_name": user_name,
        "drops": drops,
    }
    espeon_log(
        "info",
        f"Upserted member promo item cache for {user_name} in promo {promo_name}",
        context=EspeonContext.STRAYMONS,
    )

def fetch_member_promo_item_cache(promo_name: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a member's promo item from the cache.
    """
    key = (promo_name, user_id)
    return clan_promo_item_cache.get(key)