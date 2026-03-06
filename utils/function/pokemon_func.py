from config.paldea_galar_dict import dex, rarity_meta
from config.pokemon_dex import *
from config.straymons_constants import STRAYMONS__EMOJIS
from utils.database.market_value_db import (
    fetch_dex_number_cache,
    fetch_market_value_cache,
    is_pokemon_exclusive_cache,
)
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log
from config.weakness_chart import weakness_chart
enable_debug(f"{__name__}.get_display_name")


IN_GAME_MONS_LIST = (
    list(common_mons.keys())
    + list(uncommon_mons.keys())
    + list(rare_mons.keys())
    + list(superrare_mons.keys())
    + list(legendary_mons.keys())
    + list(mega_mons.keys())
    + list(gigantamax_mons.keys())
    + list(shiny_mons.keys())
    + list(shiny_mega_mons.keys())
    + list(shiny_gigantamax_mons.keys())
    + list(golden_mons.keys())
    + list(exclusive_mons.keys())
)

exclusive_mons_list = list(exclusive_mons.keys())


def get_dex_from_weakness_chart(pokemon_name):
    entry = weakness_chart.get(pokemon_name.lower())
    if entry and "dex" in entry:
        return int(entry["dex"])
    return None


def get_dex_number_by_name(name: str) -> int | None:
    """
    Returns the dex number for a given Pokémon name.
    Example: get_dex_number_by_name("flutter-mane") -> 987
    Returns None if not found.
    """

    # Try to get dex number from cache first
    formatted_name = format_names_for_market_value_lookup(name)
    dex_number = fetch_dex_number_cache(formatted_name)
    if dex_number is not None:
        return dex_number

    for num, poke_name in dex.items():
        if poke_name == name:
            return num

    if formatted_name in IN_GAME_MONS_LIST:
        # Try to get dex from all rarity dicts
        for mons_dict in [
            common_mons,
            uncommon_mons,
            rare_mons,
            superrare_mons,
            legendary_mons,
            mega_mons,
            gigantamax_mons,
            shiny_mons,
            shiny_mega_mons,
            shiny_gigantamax_mons,
            golden_mons,
            exclusive_mons,
        ]:
            if formatted_name in mons_dict:
                return mons_dict[formatted_name].get("dex")
        return get_dex_number_by_name(formatted_name)

    dex_number = get_dex_from_weakness_chart(name)
    if dex_number is not None:
        return dex_number

    return None


def strip_prefixes(pokemon_name: str):
    """
    Strip form prefixes from a Pokémon name to get the base name for market value lookup.
    Handles prefixes like "Shiny", "Mega", "Gigantamax", "Shiny Mega", etc.
    """
    prefixes = [
        "shiny mega",
        "shiny gigantamax",
        "golden mega",
        "gigantamax",
        "mega",
        "shiny",
        "golden",
    ]
    pokemon_name_lower = pokemon_name.lower()
    for prefix in prefixes:
        for sep in [" ", "-"]:
            if pokemon_name_lower.startswith(prefix + sep):
                return pokemon_name[len(prefix) + 1 :].strip()
    return pokemon_name.strip()


def get_embed_color_by_rarity(pokemon_name: str) -> int:
    rarity = get_rarity(pokemon_name)
    if rarity and rarity in rarity_meta:
        return rarity_meta[rarity]["color"]
    else:
        return 0xFFFFFF  # Default to white if rarity is unknown


def format_price_w_coin(n: int) -> str:
    """Format PokeCoin price with commas (no K/M shorthand)."""
    n = int(n)  # Ensure n is an integer
    pokecoin = STRAYMONS__EMOJIS.pokecoin
    return f"{pokecoin} {n:,}"


def get_display_name(pokemon_name: str, dex: bool = False) -> str:
    """Returns the display name of a Pokémon, optionally including the dex number."""

    debug_log(f"get_display_name called with: pokemon_name='{pokemon_name}', dex={dex}")
    rarity = get_rarity(pokemon_name)
    debug_log(f"Rarity for '{pokemon_name}': {rarity}")
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "") if rarity else ""
    debug_log(f"Rarity emoji: '{rarity_emoji}'")
    original_name = pokemon_name
    stripped_name = strip_prefixes(pokemon_name)
    debug_log(f"Stripped prefixes: '{original_name}' -> '{stripped_name}'")
    display_name = f"{rarity_emoji} {stripped_name.title()}".strip()
    debug_log(f"Initial display_name: '{display_name}'")

    if dex:
        dex_number = get_dex_number_by_name(pokemon_name)
        debug_log(f"Dex number for '{pokemon_name}': {dex_number}")
        if dex_number:
            display_name = f"{display_name} #{dex_number}"
            debug_log(f"Display name with dex: '{display_name}'")
    debug_log(f"Final display_name: '{display_name.strip()}'")
    return display_name.strip()


# enable_debug(f"{__name__}.is_mon_exclusive")
def is_mon_exclusive(pokemon: str) -> bool:
    """
    Checks if a given Pokémon is exclusive based on the exclusive_mons list or the market value cache.
    """
    debug_log(f"Checking exclusivity for: {pokemon}")
    name = pokemon.lower()
    if any(name == mon.lower() for mon in exclusive_mons_list):
        debug_log(f"{pokemon} is exclusive based on the exclusive_mons list.")
        return True
    # Check cache for exclusivity, if it's exclusive then it's not auctionable
    pokemon = format_names_for_market_value_lookup(pokemon)
    if is_pokemon_exclusive_cache(pokemon):
        debug_log(f"{pokemon} is exclusive based on the market value cache.")
        return True
    else:
        debug_log(f"{pokemon} is not exclusive based on the market value cache.")
        return False


def get_rarity(pokemon: str):
    """Determines the rarity of a given Pokemon based on the name"""

    name = pokemon.lower()
    if (
        "golden mega" in name
        and not "golden yanmega" in name
        and not "golden meganium" in name
    ):
        return "golden mega"
    elif "golden" in name:
        return "golden"
    elif "shiny" in name and (
        "gigantamax" in name or "gigantamax-" in name or "gmax-" in name
    ):
        return "shiny gigantamax"
    elif "shiny" in name and "mega" in name:
        return "shiny mega"
    elif "shiny" in name:
        return "shiny"
    elif "gigantamax" in name or "gigantamax-" in name or "gmax-" in name:
        return "gigantamax"
    elif "mega" in name and not "yanmega" in name and not "meganium" in name:
        return "mega"

    # Fallback to the list (case-insensitive)
    elif name in (mon.lower() for mon in legendary_mons):
        return "legendary"
    elif name in (mon.lower() for mon in superrare_mons):
        return "superrare"
    elif name in (mon.lower() for mon in rare_mons):
        return "rare"
    elif name in (mon.lower() for mon in uncommon_mons):
        return "uncommon"
    elif name in (mon.lower() for mon in common_mons):
        return "common"
    else:
        return None


def format_names_for_market_value_lookup(pokemon_name: str):
    """
    Format Pokémon name for market value lookup"""
    # Special log for names containing '-o'
    if "-o" in pokemon_name:
        debug_log(f"SPECIAL: '-o' detected in name: {pokemon_name!r}")
    # Special log for 'type null'
    if pokemon_name.lower().strip() == "type null":
        debug_log(f"SPECIAL: 'type null' detected: {pokemon_name!r}")
    pokemon_name = pokemon_name.lower().strip()
    if pokemon_name.startswith("sgmax "):
        # shiny gigantamax-<name>
        base = pokemon_name[6:].strip()
        result = f"shiny gigantamax-{base}"
        # debug_log(f"sgmax result: {result}")
        return result
    elif pokemon_name.startswith("gmax "):
        # gigantamax-<name>
        base = pokemon_name[5:].strip()
        result = f"gigantamax-{base}"
        # debug_log(f"gmax result: {result}")
        return result
    elif "smega" in pokemon_name:
        result = pokemon_name.replace("smega", "shiny mega").replace("-", " ")
        # debug_log(f"smega result: {result}")
        return result
    elif "mega" in pokemon_name:
        result = pokemon_name.replace("-", " ")
        # debug_log(f"mega result: {result}")
        return result
    else:
        # debug_log(f"default result: {pokemon_name}")
        return pokemon_name


def is_mon_in_game(pokemon_name: str) -> bool:
    """Check if a Pokémon is in the game."""
    name_lower = pokemon_name.lower()
    if name_lower in IN_GAME_MONS_LIST:
        return True
    # Fallback to check if the formatted name is in the market value cache
    pokemon_name_formatted = format_names_for_market_value_lookup(pokemon_name)
    market_value = fetch_market_value_cache(pokemon_name_formatted)
    if market_value is not None:
        return True
    return False
