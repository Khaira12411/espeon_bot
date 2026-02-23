# 🟣────────────────────────────────────────────
#           💜 /market-alert toggle 💜
# 🟣────────────────────────────────────────────

import discord

from config.emojis import PokeCoin
from utils.essentials.loader import pretty_defer
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    toggle_market_alert_notify,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import espeon_log


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › Market Alert Toggle ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def toggle_market_alert_func(
    bot, interaction: discord.Interaction, pokemon: str, value: bool
):
    """
    Toggle 'notify' on/off for a specific Pokemon/Dex alert or all alerts.
    Sends the resulting embed directly to the interaction.
    """
    from utils.cache.market_alert_cache import update_user_alerts_in_cache

    user = interaction.user
    user_id = user.id
    loader = await pretty_defer(
        interaction=interaction, content="Toggling market alert...", ephemeral=False
    )

    try:
        # ── Handle ALL case ──
        if pokemon.lower() == "all":
            updated_count = await toggle_market_alert_notify(bot, user_id, value, "all")
            # Bulk update cache for this user
            update_user_alerts_in_cache(user_id=user_id, new_notify=value)
            embed = discord.Embed(
                title="💜 Market Alerts Updated",
                description=f"Toggled **{updated_count} alert(s)** to {'✅ Enabled' if value else '❌ Disabled'}.",
                color=0xFF99FF,
            )
            await loader.success(content="", embed=embed)
            espeon_log(
                "sent",
                f"Toggled {updated_count} alerts for user {user_id} (ALL)",
                source="MarketAlert",
            )
            return

        # ── Resolve Pokemon name & Dex ──
        pokemon_title = pokemon.title()
        target_name, display_name, dex_number, error = resolve_pokemon_input(
            pokemon_title
        )
        debug_log(
            f"Resolved: target_name={target_name}, display_name={display_name}, dex_number={dex_number}, error={error}"
        )
        if error:
            debug_log(f"Error resolving pokemon: {error}")
            await loader.error(content=error)
            return

        # ── Update notify column ──
        updated_count = await toggle_market_alert_notify(
            bot, user_id, value, target_name
        )

        # Refresh this user’s cache (single update still handled by same function)
        update_user_alerts_in_cache(
            user_id=user_id, new_notify=value, target_pokemon=target_name
        )

        if updated_count == 0:
            embed = discord.Embed(
                title="💜 No Alert Found",
                description=f"You don’t have any alert for **{display_name}**.",
                color=0xFF66CC,
            )
        else:
            embed = discord.Embed(
                title="💜 Market Alert Toggled",
                description=f"Toggled your alert for **{display_name}** "
                f"to {'✅ Enabled' if value else '❌ Disabled'}.",
                color=0xFF99FF,
            )

        await loader.success(content="", embed=embed)
        espeon_log(
            "sent",
            f"Toggled alert for user {user_id} -> {target_name} (Dex #{dex_number})",
            source="MarketAlert",
        )

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to toggle market alert for user {user_id}: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await loader.error(content=f"An unexpected error occurred: {e}")
        return
