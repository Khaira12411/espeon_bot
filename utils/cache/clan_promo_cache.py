import discord
from typing import Any, Dict, Optional
from utils.cache.cache_list import clan_promo_cache
from utils.database.clan_promo_db import fetch_active_promo
from utils.loggers.espeon_log import EspeonContext, espeon_log


async def load_active_promo_cache(bot: discord.Client):
    """
    Load the active promo from the database into the cache.
    """
    try:
        active_promo = await fetch_active_promo(bot)
        if active_promo:
            clan_promo_cache["active_promo"] = active_promo
        else:
            clan_promo_cache["active_promo"] = None
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to load active promo cache: {e}",
            context=EspeonContext.STRAYMONS,
        )


def upsert_active_promo_cache(
    name: str,
    prize: str,
    image_url: str,
    catch_rate: int,
    battle_rate: int,
    fish_rate: int,
    emoji: str,
    whitelist_role_id: Optional[int] = None,
    number_before_claim: int = 0,
    ends_on: Optional[int] = None,
):
    """
    Upsert the active promo into the cache.
    """
    clan_promo_cache["active_promo"] = {
        "name": name,
        "prize": prize,
        "image_url": image_url,
        "catch_rate": catch_rate,
        "battle_rate": battle_rate,
        "fish_rate": fish_rate,
        "emoji": emoji,
        "whitelist_role_id": whitelist_role_id,
        "number_before_claim": number_before_claim,
        "ends_on": ends_on,
    }
    espeon_log(
        "info",
        f"Upserted active promo cache: {name}",
        context=EspeonContext.STRAYMONS,
    )

def get_active_promo_cache() -> Optional[Dict[str, Any]]:
    """
    Get the active promo from the cache.
    """
    return clan_promo_cache.get("active_promo")

def delete_active_promo_cache():
    """
    Delete the active promo from the cache.
    """
    if "active_promo" in clan_promo_cache:
        del clan_promo_cache["active_promo"]
        espeon_log(
            "info",
            "Deleted active promo cache",
            context=EspeonContext.STRAYMONS,
        )