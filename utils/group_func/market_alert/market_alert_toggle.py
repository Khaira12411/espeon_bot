import discord

from config.emojis import PokeCoin  # your coin emoji
from config.weakness_chart import weakness_chart
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    toggle_market_alert_notify,
)


# 🟪────────────────────────────────────────────
#   Toggle Market Alerts
# 🟪────────────────────────────────────────────
async def toggle_market_alert_func(
    bot, user_id: int, pokemon: str, value: bool
) -> discord.Embed:
    """
    Toggle 'notify' on/off for a specific Pokémon/Dex alert or all alerts.
    """
    # ── Handle ALL case ──
    if pokemon.lower() == "all":
        updated_count = await toggle_market_alert_notify(bot, user_id, value, "all")
        await load_market_alert_cache(bot)

        return discord.Embed(
            title="💜 Market Alerts Updated",
            description=f"Toggled **{updated_count} alerts** to "
            f"{'✅ Enabled' if value else '❌ Disabled'}.",
            color=0xFF99FF,
        )

    # ── Parse Dex or Pokémon Name ──
    pokemon_name = None
    dex_number = None

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
                pokemon_name = prefix + name
                dex_number = int(input_dex)
                break

        if not pokemon_name:
            raise ValueError(f"No Pokémon found with Dex #{pokemon}")

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

        pokemon_name = prefix + base_name
        try:
            dex_number = int(pokemon)
        except ValueError:
            dex_number = int(chart_data["dex"])

    # ── Update notify column ──
    updated_count = await toggle_market_alert_notify(bot, user_id, value, pokemon_name)
    await load_market_alert_cache(bot)

    if updated_count == 0:
        return discord.Embed(
            title="💜 No Alert Found",
            description=f"You don’t have any alert for **{pokemon_name} (Dex #{dex_number})**.",
            color=0xFF66CC,
        )

    return discord.Embed(
        title="💜 Market Alert Toggled",
        description=f"Toggled your alert for **{pokemon_name} (Dex #{dex_number})** "
        f"to {'✅ Enabled' if value else '❌ Disabled'}.",
        color=0xFF99FF,
    )
