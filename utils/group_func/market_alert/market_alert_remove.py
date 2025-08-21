# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain: Remove 💜
# ─────────────────────────────────────────────

import discord

from config.emojis import PokeCoin  # your coin emoji
from config.weakness_chart import weakness_chart
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    remove_all_market_alerts,
    remove_market_alert,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input


# ─────────────────────────────────────────────
#           💜 Remove Market Alert
# ─────────────────────────────────────────────
async def remove_market_alert_func(bot, user_id: int, pokemon: str) -> discord.Embed:
    """
    Removes a market alert for a user.
    - Can take Pokémon name or Dex number.
    - If 'all' is passed, removes all alerts for the user.
    Returns a confirmation embed.
    """
    # ── Handle "all" ──
    if pokemon.lower() == "all":
        removed_count = await remove_all_market_alerts(bot, user_id)
        await load_market_alert_cache(bot)
        embed = discord.Embed(
            title="💜 Market Alerts Removed!",
            description=f"All your market alerts have been removed successfully! ({removed_count} removed)",
            color=0xFF99FF,
        )
        embed.set_footer(text="You will no longer receive alerts 💜")
        return embed

    # ── Resolve Pokémon name & Dex ──
    pokemon_title = pokemon.title()

    # If input matches a Mega Pokémon format, skip resolve
    if any(
        pokemon_title.startswith(f"{prefix}Mega ")
        for prefix in ["", "Shiny ", "Golden "]
    ):
        target_name = pokemon_title
        target_dex = None  # optionally, set to None if you won't use Dex here
    else:
        try:
            target_name, target_dex = resolve_pokemon_input(pokemon)
            print(f"target name: {target_name}")
        except ValueError as e:
            raise ValueError(str(e))

    # ── Remove the alert ──
    removed_count = await remove_market_alert(bot, user_id, target_name)
    await load_market_alert_cache(bot)

    # ── Build confirmation embed ──
    if removed_count > 0:
        embed = discord.Embed(
            title="💜 Market Alert Removed!",
            description=f"Removed {removed_count} alert(s) for **{target_name}**.",
            color=0xFF99FF,
        )
        embed.set_footer(text="You will no longer receive alerts for this Pokémon 💜")
    else:
        embed = discord.Embed(
            title="❌ No Alert Found",
            description=f"No active alert found for **{target_name}**.",
            color=0xFF99FF,
        )
        embed.set_footer(text="Try checking your spelling or using the Dex number 💜")

    return embed
