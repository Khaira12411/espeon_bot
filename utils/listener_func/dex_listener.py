# --------------------
#  Market embed parser utility
# --------------------
import re
from typing import Optional, Tuple

import discord

from utils.database.market_value_db import (
    fetch_dex_number_cache,
    fetch_image_link_cache,
    fetch_pokemon_exclusivity_cache,
    update_dex_number,
    update_is_exclusive,
    update_rarity,
    upsert_image_link,
    fetch_rarity_cache,
)
from utils.function.pokemon_func import is_mon_exclusive
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log

# enable_debug(f"{__name__}.dex_listener")


def extract_pokemon_name_and_dex(text):
    match = re.match(r"(.+?)\s*#(\d+)", text)
    if match:
        name = match.group(1).strip()
        dex = match.group(2).strip()
        return name, dex
    else:
        return text.strip(), None


def extract_rarity_from_embed(embed) -> str:
    """
    Extracts the rarity text or emoji name from the 'Rarity' field in a Discord embed object.
    Returns the rarity as a string (e.g., 'Uncommon').
    """
    # Find the 'Rarity' field in the embed
    for field in getattr(embed, "fields", []):
        if field.get("name", "").lower() == "rarity":
            value = field.get("value", "")
            # Try to extract emoji name from custom emoji
            match = re.search(r"<:([a-zA-Z0-9_]+):[0-9]+>", value)
            if match:
                return match.group(1)
            return value.strip()
    # If not found, return empty string
    return ""


async def dex_listener(bot, message: discord.Message):
    """Listens to dex command and updates the image link in the market value cache if it differs from the one in the command output."""
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    embed_title = embed.title if embed.title else ""
    embed_author_name = embed.author.name if embed.author else ""
    pokemon_name, dex_number = extract_pokemon_name_and_dex(embed_author_name)
    if not pokemon_name:
        debug_log(
            f"Could not extract pokemon name from embed title: '{embed_author_name}'"
        )
        return
    embed_image_url = embed.image.url if embed.image else None
    image_link_cache = fetch_image_link_cache(pokemon_name)
    existing_exclusive_status = fetch_pokemon_exclusivity_cache(pokemon_name)
    is_exclusive = is_mon_exclusive(pokemon_name)
    if existing_exclusive_status != is_exclusive and is_exclusive == False:
        new_exclusive = is_exclusive
        await update_is_exclusive(bot, pokemon_name, new_exclusive)
    else:
        new_exclusive = existing_exclusive_status
    if embed_image_url and image_link_cache != embed_image_url:
        await upsert_image_link(bot, pokemon_name, embed_image_url, new_exclusive)
        debug_log(f"Updated image link for {pokemon_name} to {embed_image_url}.")
        espeon_log(
            "info",
            f"Updated image link for {pokemon_name} to {embed_image_url}.",
        )
    old_dex_number = fetch_dex_number_cache(pokemon_name)
    if dex_number and str(old_dex_number) != str(dex_number):
        dex_number = int(dex_number)
        await update_dex_number(bot, pokemon_name, dex_number)
        debug_log(f"Updated dex number for {pokemon_name} to {dex_number}.")
        espeon_log(
            "info",
            f"Updated dex number for {pokemon_name} to {dex_number}.",
        )
    old_rarity = fetch_rarity_cache(pokemon_name)
    if not old_rarity or old_rarity == "unknown":
        rarity = extract_rarity_from_embed(embed)
        if rarity and rarity != "unknown":
            await update_rarity(bot, pokemon_name, rarity)
            debug_log(f"Updated rarity for {pokemon_name} to {rarity}.")
            espeon_log(
                "info",
                f"Updated rarity for {pokemon_name} to {rarity}.",
            )
