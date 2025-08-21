import discord

from config.emojis import PokeCoin  # your coin emoji
from config.weakness_chart import weakness_chart
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    toggle_market_alert_notify,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input

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

    # ── Resolve Pokémon name & Dex ──
    pokemon_title = pokemon.title()

    # If input matches a Mega Pokémon format, skip resolve
    if any(
        pokemon_title.startswith(f"{prefix}Mega ")
        for prefix in ["", "Shiny ", "Golden "]
    ):
        target_name = pokemon_title
        dex_number = None  # optionally, set to None if you won't use Dex here
        temp_name, dex_number = resolve_pokemon_input(pokemon)
    else:
        try:
            target_name, dex_number = resolve_pokemon_input(pokemon)
        except ValueError as e:
            raise ValueError(str(e))

    # ── Update notify column ──
    updated_count = await toggle_market_alert_notify(bot, user_id, value, target_name)
    await load_market_alert_cache(bot)

    if updated_count == 0:
        return discord.Embed(
            title="💜 No Alert Found",
            description=f"You don’t have any alert for **{target_name} (Dex #{dex_number})**.",
            color=0xFF66CC,
        )

    return discord.Embed(
        title="💜 Market Alert Toggled",
        description=f"Toggled your alert for **{target_name} (Dex #{dex_number})** "
        f"to {'✅ Enabled' if value else '❌ Disabled'}.",
        color=0xFF99FF,
    )
