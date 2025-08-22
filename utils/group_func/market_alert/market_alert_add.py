# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain 💜
# ─────────────────────────────────────────────

import discord

from config.emojis import PokeCoin  # your coin emoji
from config.weakness_chart import weakness_chart
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    insert_dex_alert,
    insert_name_alert,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input


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
    Handles:
    - Numeric Dex input (normal, shiny, golden, special forms)
    - Name input (with hyphens, spaces, mega forms)
    """

    # ── Resolve Pokémon name and Dex ──
    try:
        pokemon_name, dex_number = resolve_pokemon_input(pokemon)
    except ValueError as e:
        raise ValueError(str(e))

    # ── Validate max price ──
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
    from utils.cache.market_alert_cache import load_market_alert_cache

    await load_market_alert_cache(bot)

    # ── Build confirmation embed ──
    role_mention = f" <@&{role_id}>" if role_id else ""
    embed = discord.Embed(
        title="💜 Market Alert Added!",
        description=f"Your market alert has been successfully created!{role_mention}",
        color=0xFF99FF,
    )
    embed.add_field(
        name="Pokémon",
        value=f"{pokemon_name.title()} (Dex #{dex_number})",
        inline=False,
    )
    embed.add_field(name="Max Price", value=f"{PokeCoin} {max_price:,}", inline=False)
    embed.add_field(
        name="Channel", value=f"<#{channel_id}>{role_mention}", inline=False
    )

    embed.set_footer(text="You'll be notified when a Pokémon matches your alert 💜")
    return embed
