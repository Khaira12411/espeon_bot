# -------------------- Pokemon Autocomplete --------------------
import ast
import os

import discord
from discord import app_commands

from utils.group_func.market_alert.db_func.market_alert_db_func import *

# -------------------- Config --------------------
WEAKNESS_CHART_FILE = os.path.join("config", "weakness_chart.py")


def format_price(n: int) -> str:
    """Format PokeCoin price into K/M shorthand."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# -------------------- Load weakness_chart --------------------
def load_weakness_chart():
    with open(WEAKNESS_CHART_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = ast.parse(content)
    weakness_chart = None
    for node in parsed.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "weakness_chart":
                weakness_chart = ast.literal_eval(node.value)

    if weakness_chart is None:
        raise ValueError("Could not find weakness_chart dict in the file.")

    return weakness_chart


WEAKNESS_CHART = load_weakness_chart()


# -------------------- Autocomplete Function --------------------
from discord import app_commands


# -------------------- User Alerts Autocomplete --------------------
async def user_alerts_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """
    Autocomplete for the user's own market alerts from cache.
    Choice.name = "Name #Dex — price"
    Choice.value = "Name" only
    """
    from utils.cache.market_alert_cache import fetch_user_alerts_from_cache

    user_id = interaction.user.id

    # Fetch all alerts for this user from cache
    try:
        rows = fetch_user_alerts_from_cache(user_id)
    except Exception:
        rows = []

    current = (current or "").lower().strip()
    results: list[app_commands.Choice[str]] = []

    for row in rows:
        name = row["pokemon"].title()
        dex = row.get("dex_number")
        max_price = row.get("max_price", 0)

        display = f"{name} #{dex}"

        # match input against name or dex
        if not current or current in name.lower() or current in str(dex):
            results.append(app_commands.Choice(name=display, value=name))

        if len(results) >= 25:  # Discord limit
            break

    # fallback
    if not results:
        results.append(app_commands.Choice(name="No matches found", value=current))

    return results


# put near top of your module
import re
from typing import Optional, Tuple, List
from discord import app_commands


# build quick indexes once (call at import)
def build_weakness_indexes(weakness_chart: dict):
    dex_to_key = {}
    key_normalized = {}  # normalized name -> key (helps matching)
    for key, data in weakness_chart.items():
        dex_raw = data.get("dex")
        try:
            dex_int = int(dex_raw) if dex_raw is not None else None
        except Exception:
            dex_int = None

        if dex_int is not None:
            dex_to_key[dex_int] = key

        # normalized variants for lookups
        norm = key.lower()
        norm = norm.replace("-", " ").replace("_", " ").strip()
        key_normalized[norm] = key
        # also store punctuation-free version
        simple = re.sub(r"[^\w\s]", "", norm)
        key_normalized[simple] = key

    return dex_to_key, key_normalized


# create indexes (replace WEAKNESS_CHART with your dict)
DEX_TO_KEY, KEY_NORMALIZED = build_weakness_indexes(WEAKNESS_CHART)

# Pre-build a clean list for fast autocomplete
POKEMON_LIST: list[tuple[str, int]] = [
    (key.title(), int(data.get("dex", 0)))
    for key, data in WEAKNESS_CHART.items()
    if data.get("dex") is not None
]


# -------------------------- Autocomplete function --------------------------
async def old_pokemon_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    current = (current or "").lower().strip()
    results: list[app_commands.Choice[str]] = []

    for key, data in WEAKNESS_CHART.items():
        dex_raw = data.get("dex")
        if not dex_raw:
            continue
        try:
            dex_int = int(dex_raw)
        except ValueError:
            continue

        name = key.title()
        display = f"{name} #{dex_int}"

        if not current or current in name.lower() or current in str(dex_int):
            results.append(app_commands.Choice(name=display, value=name))

        if len(results) >= 25:  # Discord limit
            break

    # Always return something
    return results or [app_commands.Choice(name="No matches found", value=current)]


# -------------------------- Clean Pokemon Autocomplete --------------------------
import re
from discord import app_commands

# Pre-build a normalized list for autocomplete
POKEMON_NORMALIZED: list[tuple[str, str, int]] = []
for name, dex in POKEMON_LIST:
    # remove punctuation & spaces for normalized lookup
    norm = re.sub(r"[^\w\s]", "", name.lower()).replace(" ", "")
    POKEMON_NORMALIZED.append((name, norm, dex))


async def pokemon_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    """
    Autocomplete Pokémon names with #Dex display.
    Fuzzy matching: punctuation & spaces ignored.
    Returns max 25 results.
    """
    current_simple = re.sub(r"[^\w\s]", "", (current or "").lower()).replace(" ", "")
    results: list[app_commands.Choice[str]] = []
    seen = set()  # prevent duplicates

    for name, norm, dex in POKEMON_NORMALIZED:
        if not current_simple or current_simple in norm:
            display = f"{name} #{dex}"
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
