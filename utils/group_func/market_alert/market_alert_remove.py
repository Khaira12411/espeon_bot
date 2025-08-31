# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain: Remove 💜
# ─────────────────────────────────────────────

from datetime import datetime

import discord

from config.aesthetic import *
from utils.group_func.market_alert.db_func.market_alert_counter import *
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    remove_all_market_alerts,
    remove_market_alert,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input
from utils.loggers.espeon_log import espeon_log
from utils.visuals.embeds.get_log_channel import get_log_channel
from utils.visuals.embeds.visual_helpers import design_embed


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
#todo add a remove all report log
    await interaction.response.defer()
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
            await interaction.edit_original_response(embed=embed)  # non-ephemeral
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
            await interaction.edit_original_response(
                f"❌ Failed to remove all alerts: {e}"
            )  # non-ephemeral
            return
    # 💜 Resolve Pokémon
    initial_dex = ""
    initial_pokemon = ""
    pokemon_title = pokemon.title()
    # Initial Values
    if pokemon.isdigit():
        initial_dex = pokemon
    else:
        initial_pokemon = pokemon.title()

    print(f"[DEBUG] Initial input: {pokemon}, title-cased: {pokemon_title}")

    try:
        if any(
            pokemon_title.startswith(f"{prefix}Mega ")
            for prefix in ["", "Shiny ", "Golden "]
        ):
            target_name = pokemon_title
            print(
                f"[DEBUG] Detected Mega form or special prefix, target_name: {target_name}"
            )
        else:
            for prefix in ["Shiny ", "Golden "]:
                if pokemon_title.startswith(prefix):
                    target_name = pokemon_title
                    place_holder_name, dex_number = resolve_pokemon_input(pokemon_title)
                else:
                    target_name, dex_number = resolve_pokemon_input(pokemon_title)
            print(
                f"[DEBUG] Resolved normally: target_name={target_name}, dex_number={dex_number}"
            )
    except ValueError as e:
        print(f"[ERROR] ValueError encountered: {e}")
        import traceback

        traceback.print_exc()
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return

    # 💜 Remove the alert
    try:
        if initial_dex:
            removed_count = await remove_market_alert(bot, user_id, initial_dex)
        else:
            removed_count = await remove_market_alert(bot, user_id, target_name.lower())
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
            display_name = target_name
            display_dex = dex_number
            if initial_pokemon.startswith(prefix):
                display_name = initial_pokemon
            elif initial_dex:
                display_dex = initial_dex

            user_embed.add_field(
                name="Pokémon",
                value=f"{display_name.title()} #{display_dex}",
                inline=False,
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
        log_channel = get_log_channel(bot=bot)
        if log_channel:
            log_embed = discord.Embed(
                title=f"{Espeon_Emoji.purple_hearts_one} Market Alert Removed",
                description=f"""- Member: {user.mention}
- Removed Pokemon: {target_name.title()} #{dex_number}""",
                color=0xFF99FF,
                timestamp=datetime.now(),
            )
            log_embed = design_embed(embed=log_embed, user=user)
        if is_staff == False:
            log_embed.add_field(
                name="Alerts Usage",
                value=f"Used: {status['alerts_used']} / Total: {status['total_alerts']} ({status['alerts_left']} left)",
                inline=False,
            )

        # 💜 Send embeds
        await interaction.edit_original_response(embed=user_embed)
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
