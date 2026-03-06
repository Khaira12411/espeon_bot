# --------------------
#  Market embed parser utility
# --------------------
import re
from typing import Optional, Tuple

import discord

from utils.database.market_value_db import (
    fetch_emoji_id_cache,
    update_emoji_id_cache,
)
from utils.function.pokemon_func import is_mon_exclusive
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log

# enable_debug(f"{__name__}.dex_listener")
# enable_debug(f"{__name__}.extract_rarity_from_embed")
emoji_map = {
    "common": "common",
    "uncommon": "uncommon",
    "rare": "rare",
    "superrare": "superrare",
    "legendary": "legendary",
    "shiny": "shiny",
    "golden": "golden",
    "shinymega": "shiny mega",
    "shinygigantamax": "shiny gigantamax",
    "mega": "mega",
    "gigantamax": "gigantamax",
    "goldenmega": "golden mega",
    "goldengigantamax": "golden gigantamax",
}


def extract_emoji_id_from_evolution_line(description: str) -> str | None:
    """
    Extracts the first emoji tag before any bolded Pokémon name in the evolution line from a description string.
    Returns the emoji tag as a string, or None if not found.
    """
    debug_log(f"Extracting emoji tag from description: {description!r}")
    # Find the evolution line section
    evo_line_match = re.search(
        r":dna: \*\*Evolution line\*\*\s*\n([^\n]+)", description
    )
    if evo_line_match:
        evo_line = evo_line_match.group(1)
        debug_log(f"Evolution line found: {evo_line!r}")
        # Now extract the emoji tag before the bolded name
        emoji_match = re.search(r"(<:[^:]+:\d+>) \*\*.+?\*\*", evo_line)
        if emoji_match:
            emoji_tag = emoji_match.group(1)
            debug_log(f"Found emoji tag: {emoji_tag}")
            return emoji_tag
        debug_log("No emoji tag found in evolution line.")
    else:
        debug_log("No evolution line found in description.")
    return None


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
    Returns the mapped rarity as a string (e.g., 'shiny gigantamax').
    """
    debug_log("Starting rarity extraction from embed.")
    fields = []
    # Try to get fields from embed object (discord.py Embed or dict)
    if hasattr(embed, "fields"):
        fields = embed.fields
        debug_log(f"Embed fields attribute found: {fields}")
    elif isinstance(embed, dict) and "fields" in embed:
        fields = embed["fields"]
        debug_log(f"Embed fields key found: {fields}")
    else:
        debug_log(f"Embed has no fields attribute or key. Embed: {embed}")
    for idx, field in enumerate(fields):
        debug_log(f"Checking field {idx}: {field}")
        name = (
            field.get("name")
            if isinstance(field, dict)
            else getattr(field, "name", None)
        )
        value = (
            field.get("value")
            if isinstance(field, dict)
            else getattr(field, "value", None)
        )
        debug_log(f"Field name: {name}, value: {value}")
        if name and name.lower() == "rarity":
            debug_log(f"Found 'Rarity' field with value: {value}")
            match = re.search(r"<:([a-zA-Z0-9_]+):[0-9]+>", value)
            if match:
                emoji_name = match.group(1)
                debug_log(f"Extracted emoji name: {emoji_name}")
                mapped_rarity = emoji_map.get(emoji_name.lower(), emoji_name)
                debug_log(f"Mapped rarity: {mapped_rarity}")
                return mapped_rarity
            debug_log(f"Returning plain rarity value: {value.strip()}")
            return value.strip()
    debug_log("'Rarity' field not found in embed.")
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
    old_emoji_id = fetch_emoji_id_cache(pokemon_name)
    if not old_emoji_id:
        emoji_id = extract_emoji_id_from_evolution_line(embed.description or "")
        if emoji_id and old_emoji_id != emoji_id:
            try:
                update_emoji_id_cache(pokemon_name, emoji_id)
                debug_log(f"Updated emoji ID for {pokemon_name} to {emoji_id}.")
            except Exception as e:
                espeon_log(
                    "warn",
                    f"⚠️ Failed to update emoji ID for {pokemon_name} to {emoji_id}: {e}",
                    exc=e,
                )
