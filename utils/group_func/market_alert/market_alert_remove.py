# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain: Remove 💜
# ─────────────────────────────────────────────

import discord

from utils.group_func.market_alert.db_func.market_alert_counter import *
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    remove_all_market_alerts,
    remove_market_alert,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input
from utils.loggers.espeon_log import espeon_log


async def remove_market_alert_func(bot, interaction: discord.Interaction, pokemon: str):
    """
    Removes a market alert for a user.
    Handles:
    - Pokémon name or Dex number
    - 'all' to remove all alerts
    Sends the confirmation embed directly to the interaction.
    """
    from utils.cache.market_alert_cache import load_market_alert_cache

    user = interaction.user
    user_id = user.id

    # 💜 Handle "all"
    if pokemon.lower() == "all":
        try:
            removed_count = await remove_all_market_alerts(bot, user_id)
            await load_market_alert_cache(bot)
            embed = discord.Embed(
                title="💜 Market Alerts Removed!",
                description=f"All your market alerts have been removed successfully! ({removed_count} removed)",
                color=0xFF99FF,
            )
            embed.set_footer(text="You will no longer receive alerts 💜")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            espeon_log(
                "sent",
                f"Removed all market alerts for user {user_id}",
                source="MarketAlert",
            )
            return
        except Exception as e:
            espeon_log(
                "error",
                f"Failed to remove all alerts: {e}",
                source="MarketAlert",
                exc=e,
                include_trace=True,
            )
            await interaction.response.send_message(
                f"❌ Failed to remove all alerts: {e}", ephemeral=True
            )
            return

    # 💜 Resolve Pokémon
    pokemon_title = pokemon.title()
    try:
        if any(
            pokemon_title.startswith(f"{prefix}Mega ")
            for prefix in ["", "Shiny ", "Golden "]
        ):
            target_name = pokemon_title
        else:
            target_name, _ = resolve_pokemon_input(pokemon)
    except ValueError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return

    # 💜 Remove the alert
    try:
        removed_count = await remove_market_alert(bot, user_id, target_name)
        await load_market_alert_cache(bot)

        # 💜 Refund one alert
        status = await refund_market_alert(bot=bot, user=user)

        # 💜 User embed
        if removed_count > 0:
            user_embed = discord.Embed(
                title="💜 Market Alert Removed!",
                description=f"{status['message']}",
                color=0xFF99FF,
            )
            user_embed.add_field(
                name="Pokémon", value=f"{target_name.title()}", inline=False
            )
            user_embed.set_footer(
                text="You will no longer receive alerts for this Pokémon 💜"
            )
        else:
            user_embed = discord.Embed(
                title="❌ No Alert Found",
                description=f"No active alert found for **{target_name}**.\n{status['message']}",
                color=0xFF99FF,
            )
            user_embed.set_footer(
                text="Try checking your spelling or using the Dex number 💜"
            )
        clan_staff = interaction.guild.get_role(STRAYMONS__ROLES.clan_staff)
        is_staff = False
        if clan_staff in user.roles:
            is_staff = True
        # 💜 Log embed
        LOG_CHANNEL_ID = (
            STRAYMONS__TEXT_CHANNELS.server_logs
        )  # replace with your log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="💜 Market Alert Removed",
                description=f"{user.display_name} removed alert for {target_name.title()}",
                color=0xFF99FF,
            )
        if is_staff == False:
            log_embed.add_field(
                name="Alerts Usage",
                value=f"Used: {status['alerts_used']} / Total: {status['total_alerts']} ({status['alerts_left']} left)",
                inline=False,
            )
            
        # 💜 Send embeds
        await interaction.response.send_message(embed=user_embed, ephemeral=True)
        espeon_log(
            "sent",
            f"Removed {removed_count} market alert(s) for user {user_id} -> {target_name}",
            source="MarketAlert",
        )
        if log_channel:
            await log_channel.send(embed=log_embed)

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to remove alert: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.response.send_message(
            f"❌ Failed to remove alert: {e}", ephemeral=True
        )
