# inside get_pokemon_gif.py
from typing import Literal

from config.pokemon_gifs import *
from utils.loggers.espeon_log import EspeonContext, espeon_log

hyphen_mon_names = [
    "jangmo-o",
    "hakamo-o",
    "kommo-o",
    "tapu-koko",
    "tapu-lele",
    "tapu-bulu",
    "tapu-fini",
]


def get_pokemon_gif(input_name: str):
    """
    Returns the pokemon gif
    """
    original_input = input_name
    shiny = False
    golden = False
    form: Literal["regular", "mega", "gmax"] = "regular"
    region_suffix = ""

    # Normalize input
    name_parts = input_name.lower().replace("_", "-").split()

    if "golden" in name_parts:
        golden = True
        name_parts.remove("golden")
    if "shiny" in name_parts:
        shiny = True
        name_parts.remove("shiny")

    remaining_name = "-".join(name_parts)

    regions = {
        "alolan": "-alola",
        "galarian": "-galar",
        "hisuian": "-hisui",
        "paldean": "-paldea",
    }
    for region_prefix, suffix in regions.items():
        if remaining_name.startswith(region_prefix + "-"):
            region_suffix = suffix
            remaining_name = remaining_name[len(region_prefix) + 1 :]
            break

    if remaining_name.startswith("mega-"):
        form = "mega"
        remaining_name = remaining_name.replace("mega-", "")
    elif remaining_name.startswith(("gigantamax-", "gmax-")):
        form = "gmax"
        remaining_name = remaining_name.replace("gigantamax-", "").replace("gmax-", "")

    # 🔹 Special gmax aliases
    gmax_aliases = {
        "urshifu-rapidstrike": "urs",
        "urshifu-singlestrike": "uss",
        "eternamax-eternatus": "eternatus",
    }
    if form == "gmax" and remaining_name in gmax_aliases:
        remaining_name = gmax_aliases[remaining_name]

    base_name = f"{remaining_name}{region_suffix}".lower()
    # Remove "shiny" and "golden" from the input for comparison
    compare_name = (
        input_name.lower()
        .replace("shiny", "")
        .replace("golden", "")
        .replace("_", "-")
        .strip()
    )
    compare_name = " ".join(compare_name.split())  # Remove extra spaces
    if compare_name in hyphen_mon_names:
        base_name = base_name.replace("-", "")

    attr_name = remaining_name.replace("-", "_")

    gif_url = None

    # 🔹 Golden check (priority)
    if golden:
        if form == "mega":
            golden_attr_name = f"mega_{attr_name}"
            gif_url = getattr(GOLDEN_MEGA_POKEMON_URL, golden_attr_name, None)
        elif form == "gmax":
            gif_url = getattr(GOLDEN_POKEMON_URL, f"gmax_{attr_name}", None)
        else:
            gif_url = getattr(GOLDEN_POKEMON_URL, attr_name, None)

    # 🔹 Shiny check (priority, same idea as golden)
    if shiny and not gif_url:
        if form == "mega":
            shiny_attr_name = f"mega_{attr_name}"
            gif_url = getattr(SHINY_POKEMON_URL, shiny_attr_name, None)
        elif form == "gmax":
            gif_url = getattr(SHINY_POKEMON_URL, f"gmax_{attr_name}", None)
        else:
            gif_url = getattr(SHINY_POKEMON_URL, attr_name, None)

    # 🔹 Fallbacks
    if not gif_url:
        if form == "gmax":
            gif_url = getattr(
                SHINY_GMAX_URL if shiny else REGULAR_GMAX_URL, attr_name, None
            )
        else:
            gif_url = getattr(REGULAR_POKEMON_URL, attr_name, None)

    # 🔹 Last resort → showdown sprite
    if not gif_url:
        shiny_prefix = "ani-shiny" if shiny else "xyani"
        suffix = "" if form == "regular" else f"-{form}"
        # Special handling for Mega Mewtwo and Mega Charizard forms
        if form == "mega":
            if base_name in ["mewtwo-y", "mewtwo-megay"]:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/mewtwo-megay.gif?quality=lossless"
            elif base_name in ["mewtwo-x", "mewtwo-megax"]:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/mewtwo-megax.gif?quality=lossless"
            elif base_name in ["charizard-x", "charizard-megax"]:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/charizard-megax.gif?quality=lossless"
            elif base_name in ["charizard-y", "charizard-megay"]:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/charizard-megay.gif?quality=lossless"
            else:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/{base_name}{suffix}.gif?quality=lossless"

        elif "primal" in base_name:
            # Make it groudon-primal or kyogre-primal
            if "groudon" in base_name:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/groudon-primal.gif?quality=lossless"
            elif "kyogre" in base_name:
                gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/kyogre-primal.gif?quality=lossless"
            elif "dialga" in base_name:
                gif_url = REGULAR_POKEMON_URL.primal_dialga
                
        elif "ash-greninja" in base_name:
            gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/greninja-ash.gif?quality=lossless"
        else:
            gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/{base_name}{suffix}.gif?quality=lossless"

    gif_name = f"{'golden ' if golden else ''}{'shiny ' if shiny else ''}{form + ' ' if form != 'regular' else ''}{remaining_name}"

    error = None
    if not gif_url:
        error = f"Cannot find Pokemon GIF for '{original_input}'"

    espeon_log(
        tag="debug" if gif_url else "error",
        message=(f"Fetched GIF URL for '{gif_name}': {gif_url}" if gif_url else error),
    )
    return gif_url
