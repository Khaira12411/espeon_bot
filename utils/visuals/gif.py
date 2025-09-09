import discord
from discord.ext import commands
from utils.loggers.espeon_log import espeon_log, EspeonContext
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from shared_utils.pokemon_utils.pokemon_gif import get_pokemon_gif

# Example fallback list
from config.pokemon_gifs import *
error_channel_id = STRAYMONS__TEXT_CHANNELS.error_logs


# Add a global cache at the top of your file
_pokemon_gif_cache: dict[str, str] = {}


async def fetch_pokemon_gif(pokemon: str) -> str | None:
    """Fetches a Pokémon GIF URL or returns None if missing, with caching."""

    # normalize name
    key = pokemon.lower().replace("_", "-")

    # ✅ Return cached URL if it exists
    if key in _pokemon_gif_cache:
        return _pokemon_gif_cache[key]

    # fetch using your existing function
    gif_data = await get_pokemon_gif(pokemon)
    gif_url = gif_data.get("gif_url")

    if gif_url:
        _pokemon_gif_cache[key] = gif_url  # store in cache
        return gif_url

    # log if missing
    espeon_log(
        tag="error",
        message=f"Cannot find Pokémon GIF for '{pokemon}'",
        context=EspeonContext.STRAYMONS,
        source="GIF Embed",
    )
    return None


# -------------------- Main Function (Gmax aware with Urshifu + Golden) --------------------
async def insert_pokemon_gif_embed(
    input_name: str,
    bot: commands.Bot,
    embed: discord.Embed,
    is_thumbnail: bool = True,
    context=None,
) -> discord.Embed:
    """
    Adds a Pokémon GIF to the provided embed.
    - Handles shiny, mega, gmax, alolan, galarian
    - Uses hardcoded Gmax maps if Showdown URLs might not exist
    - Special Gmax cases like Urshifu
    - Detects 'golden' and uses GOLDEN_POKEMON_LIST
    """
    original_input = input_name
    shiny = False
    golden = False
    form = "regular"
    region_suffix = ""

    # Normalize
    name_parts = input_name.lower().replace("_", "-").split()

    # Detect golden
    if "golden" in name_parts:
        golden = True
        name_parts.remove("golden")

    # Detect shiny
    if "shiny" in name_parts:
        shiny = True
        name_parts.remove("shiny")

    # Regional forms
    if "alolan" in name_parts:
        region_suffix = "-alola"
        name_parts.remove("alolan")
    elif "galarian" in name_parts:
        region_suffix = "-galar"
        name_parts.remove("galarian")

    # Mega / Gigantamax
    remaining_name = "-".join(name_parts)
    if remaining_name.startswith("mega-"):
        form = "mega"
        remaining_name = remaining_name.replace("mega-", "")
    elif remaining_name.startswith("gigantamax-") or remaining_name.startswith("gmax-"):
        form = "gmax"
        remaining_name = remaining_name.replace("gigantamax-", "").replace("gmax-", "")

    base_name = remaining_name + region_suffix

    # -------------------- Special Gmax Cases --------------------
    gmax_aliases = {"urshifu-rapidstrike": "urs", "urshifu-singlestrike": "uss"}
    if form == "gmax" and remaining_name in gmax_aliases:
        remaining_name = gmax_aliases[remaining_name]

    # -------------------- Determine GIF URL --------------------
    gif_url = None

    # 1️⃣ Try to fetch from class based on golden/regular
    if golden:
        normalized_name = remaining_name.replace("-", "_")
        gif_url = getattr(GOLDEN_POKEMON_URL, normalized_name, None)
    else:
        gif_url = getattr(REGULAR_POKEMON_URL, remaining_name, None)

    # 2️⃣ Handle Gmax separately using hardcoded maps
    if form == "gmax":
        if shiny:
            gif_url = getattr(SHINY_GMAX_URL, remaining_name, None)
        else:
            gif_url = getattr(REGULAR_GMAX_URL, remaining_name, None)

    # 3️⃣ Otherwise, fallback to building Showdown URL
    if not gif_url:
        shiny_prefix = "ani-shiny" if shiny else "xyani"
        suffix = "" if form == "regular" else f"-{form}"
        gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/{base_name}{suffix}.gif?quality=lossless"

    # -------------------- Log error if GIF is missing --------------------
    if not gif_url:
        espeon_log(
            "error",
            f"Cannot find Pokémon GIF for '{original_input}'",
            bot=bot,
            context=context or EspeonContext.STRAYMONS,
            source="GIF Embed",
        )

    # -------------------- Add GIF to Embed --------------------
    if gif_url:
        if is_thumbnail:
            embed.set_thumbnail(url=gif_url)
        else:
            embed.set_image(url=gif_url)
    else:
        # Send to error channel without breaking the embed
        if error_channel_id:
            try:
                error_channel = bot.get_channel(error_channel_id)
                if error_channel:
                    await error_channel.send(
                        f"⚠️ Could not find GIF for `{original_input}`."
                    )
            except Exception:
                pass

    return embed
