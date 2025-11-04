# -------------------- 🐾 Pokemon Autocomplete Module -------------------- #


import re

import discord
from discord import app_commands

from utils.group_func.market_alert.db_func.market_alert_db_func import *

# ==================== 💠 Config ==================== #
# WEAKNESS_CHART_FILE = os.path.join("config", "weakness_chart.py")


def format_price(n: int) -> str:
    """Format PokeCoin price into K/M shorthand."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ==================== 📖 Load Weakness Chart ==================== #
from config.weakness_chart import weakness_chart as WEAKNESS_CHART


# ==================== 🗂 Build Weakness Indexes ==================== #
def build_weakness_indexes(weakness_chart: dict):
    dex_to_key = {}
    key_normalized = {}
    for key, data in weakness_chart.items():
        dex_raw = data.get("dex")
        try:
            dex_int = int(dex_raw) if dex_raw is not None else None
        except Exception:
            dex_int = None

        if dex_int is not None:
            dex_to_key[dex_int] = key

        norm = key.lower().replace("-", " ").replace("_", " ").strip()
        key_normalized[norm] = key
        simple = re.sub(r"[^\w\s]", "", norm)
        key_normalized[simple] = key

    return dex_to_key, key_normalized


DEX_TO_KEY, KEY_NORMALIZED = build_weakness_indexes(WEAKNESS_CHART)

# Pre-build clean list
POKEMON_LIST: list[tuple[str, int]] = [
    (key.title(), int(data.get("dex", 0)))
    for key, data in WEAKNESS_CHART.items()
    if data.get("dex") is not None
]


# ==================== 🐉 Unified Mega/Golden/Shiny Formatter ==================== #
POKEMON_NORMALIZED: list[tuple[str, str, int]] = []
for name, dex in POKEMON_LIST:
    norm = re.sub(r"[^\w\s]", "", name.lower()).replace(" ", "")
    POKEMON_NORMALIZED.append((name, norm, dex))


def format_display_name(raw_name: str) -> str:
    """
    Clean up Pokemon display names for autocomplete:
    - Remove dash only for Mega forms (Mega-Abomasnow → Mega Abomasnow)
    - Capitalize properly
    - Keep golden/shiny prefixes untouched
    """
    clean_name = raw_name.lower()

    # Handle Mega form
    if "mega-" in clean_name:
        clean_name = clean_name.replace("mega-", "mega ")

    # Capitalize all words
    display_name = " ".join(word.capitalize() for word in clean_name.split())

    return display_name


# ==================== 🌟 Autocomplete Functions ==================== #
async def pokemon_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """
    Autocomplete Pokemon names with #Dex display.
    Matches both names and dex numbers.
    """
    current_simple = re.sub(r"[^\w\s]", "", (current or "").lower()).replace(" ", "")
    results: list[app_commands.Choice[str]] = []
    seen = set()

    # Check if input looks numeric (dex search)
    dex_query = None
    if current_simple.isdigit():
        try:
            dex_query = int(current_simple)
        except ValueError:
            dex_query = None

    for name, norm, dex in POKEMON_NORMALIZED:
        # Match by name
        if not current_simple or current_simple in norm:
            display_name = format_display_name(name)
            display = f"{display_name} #{dex}"
            if display not in seen:
                results.append(app_commands.Choice(name=display.title(), value=name))
                seen.add(display)

        # Match by dex number
        if dex_query is not None and dex_query == dex:
            display_name = format_display_name(name)
            display = f"{display_name} #{dex}"
            if display not in seen:
                results.append(app_commands.Choice(name=display, value=name))
                seen.add(display)

        if len(results) >= 25:
            break

    if not results:
        results.append(
            app_commands.Choice(name="No matches found", value=current or "")
        )

    return results


async def user_alerts_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """
    Autocomplete for the user's own market alerts from cache.
    Choice.name = "Name #Dex — price"
    Choice.value = "Name" only
    Matches both names and dex numbers.
    """
    from utils.cache.market_alert_cache import fetch_user_alerts_from_cache

    user_id = interaction.user.id
    try:
        rows = fetch_user_alerts_from_cache(user_id)
    except Exception:
        rows = []

    current = (current or "").lower().strip()
    results: list[app_commands.Choice[str]] = []

    # Check if input is numeric
    dex_query = None
    if current.isdigit():
        try:
            dex_query = int(current)
        except ValueError:
            dex_query = None

    for row in rows:
        raw_name = row["pokemon"]
        name = format_display_name(raw_name)
        dex = row.get("dex_number")
        max_price = row.get("max_price", 0)

        display = f"{name} #{dex}"

        if (
            not current
            or current in name.lower()
            or (dex is not None and current in str(dex))
            or (dex_query is not None and dex_query == dex)
        ):
            results.append(app_commands.Choice(name=display.title(), value=raw_name))

        if len(results) >= 25:
            break

    if not results:
        results.append(app_commands.Choice(name="No matches found", value=current))

    return results
