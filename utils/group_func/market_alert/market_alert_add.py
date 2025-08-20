# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain 💜
# ─────────────────────────────────────────────

import discord
from config.weakness_chart import weakness_chart
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    insert_dex_alert,
    insert_name_alert,
)
from config.emojis import PokeCoin  # your coin emoji


async def add_market_alert_func(
    bot,
    user_id: int,
    pokemon: str,
    max_price: int,
    channel_id: int,
    role_id: int = None,
    notify: bool = True,
) -> discord.Embed:
    """
    Adds a new market alert and returns a confirmation embed.
    """

    # ── Determine Pokémon name and Dex number ──
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

    try:
        max_price = int(max_price)
    except ValueError:
        raise ValueError("Max price must be an integer.")

    # ── Insert into database and refresh cache ──
    await insert_name_alert(
        bot, user_id, pokemon_name, dex_number, max_price, channel_id, role_id, notify
    )
    await insert_dex_alert(
        bot, user_id, pokemon_name, dex_number, max_price, channel_id, role_id, notify
    )
    await load_market_alert_cache(bot)

    # ── Build confirmation embed ──
    role_mention = f" <@&{role_id}>" if role_id else ""
    embed = discord.Embed(
        title="💜 Market Alert Added!",
        description=f"Your market alert has been successfully created!{role_mention}",
        color=0xFF99FF,
    )
    embed.add_field(
        name="Pokémon", value=f"{pokemon_name} (Dex #{dex_number})", inline=False
    )
    embed.add_field(name="Max Price", value=f"{PokeCoin} {max_price:,}", inline=False)
    embed.add_field(
        name="Channel", value=f"<#{channel_id}>{role_mention}", inline=False
    )

    embed.set_footer(text="You'll be notified when a Pokémon matches your alert 💜")

    return embed
