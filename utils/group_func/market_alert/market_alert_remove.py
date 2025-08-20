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
    removed_count = 0
    target_name = None
    target_dex = None

    # Handle "all"
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

    # ── Determine Pokémon name and Dex number ──
    if str(pokemon).isdigit():
        input_dex = str(pokemon)
        first_digit = input_dex[0]

        if first_digit == "9":
            base_dex = int(input_dex[1:])
            prefix = "Golden "
        elif first_digit == "1" and len(input_dex) > 3:
            base_dex = int(input_dex[1:])
            prefix = "Shiny "
        else:
            base_dex = int(input_dex)
            prefix = ""

        for name, data in weakness_chart.items():
            chart_dex = int(str(data.get("dex")).lstrip("0"))
            if chart_dex == base_dex:
                target_name = prefix + name
                target_dex = int(input_dex)
                break

        if not target_name:
            raise ValueError(f"No Pokémon found with Dex #{pokemon}")

        removed_count = await remove_market_alert(bot, user_id, str(target_dex))

    else:
        pokemon_name_input = pokemon.lower()
        prefix = ""
        if pokemon_name_input.startswith("golden "):
            prefix = "Golden "
            base_name = pokemon_name_input[7:]
        elif pokemon_name_input.startswith("shiny "):
            prefix = "Shiny "
            base_name = pokemon_name_input[6:]
        else:
            base_name = pokemon_name_input

        chart_data = weakness_chart.get(base_name)
        if not chart_data or "dex" not in chart_data:
            raise ValueError(f"No Pokémon found with name {base_name}")

        target_name = prefix + base_name
        try:
            target_dex = int(pokemon)
        except ValueError:
            target_dex = int(chart_data["dex"])

        removed_count = await remove_market_alert(bot, user_id, target_name)

    # Refresh cache
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
