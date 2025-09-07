# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain: Remove 💜
# ─────────────────────────────────────────────

from datetime import datetime

import discord

from config.aesthetic import *
from utils.essentials.loader import pretty_defer
from utils.group_func.market_alert.db_func.market_alert_counter import *
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    fetch_user_alerts,
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
    Uses pretty_defer loader: runs full workflow first, then updates loader once with final result.
    """
    from utils.cache.market_alert_cache import load_market_alert_cache

    user = interaction.user
    user_id = user.id
    removed_alerts: list[tuple[str, str]] = []
    footer_text = "💜 You will no longer receive alerts for these Pokémon"
    # 💜 Start loader
    loader = await pretty_defer(
        interaction, content="Processing market alert removal..."
    )

    try:
        # 💜 SEPARATE BRANCH FOR "ALL"
        if pokemon.lower() == "all":
            # 💜 Fetch all alerts
            user_alerts = await fetch_user_alerts(bot, user_id)

            if not user_alerts:
                await loader.stop(content=f"❌ You have no active market alerts.")
                return

            removed_alerts = [
                (alert["pokemon"].title(), alert["dex_number"]) for alert in user_alerts
            ]

            # 💜 Remove all alerts
            await remove_all_market_alerts(bot, user_id)

            # 💜 Refresh cache and refund
            await load_market_alert_cache(bot)
            status = await refund_market_alert(bot=bot, user=user)

        else:
            # 💜 EXISTING SINGLE POKÉMON LOGIC
            pokemon_title = pokemon.title()
            if pokemon.isdigit():
                target_key = pokemon
            else:
                target_key = pokemon_title

            try:
                if any(
                    pokemon_title.startswith(f"{prefix}Mega ")
                    for prefix in ["", "Shiny ", "Golden "]
                ):
                    target_name = pokemon_title
                    dex_number = None
                else:
                    for prefix in ["Shiny ", "Golden "]:
                        if pokemon_title.startswith(prefix):
                            target_name = pokemon_title
                            _, dex_number = resolve_pokemon_input(pokemon_title)
                        else:
                            target_name, dex_number = resolve_pokemon_input(
                                pokemon_title
                            )
            except ValueError as e:
                raise ValueError(f"{e}")

            # 💜 Check if alert exists before trying to remove
            user_alerts = await fetch_user_alerts(bot, user_id)
            exists = False
            for alert in user_alerts:
                if pokemon.isdigit() and alert["dex_number"] == int(pokemon):
                    exists = True
                    break
                elif (
                    not pokemon.isdigit()
                    and alert["pokemon"].lower() == target_name.lower()
                ):
                    exists = True
                    break

            if not exists:
                await loader.stop(
                    content=f"❌ No active alert found for **{pokemon_title}**."
                )
                return

            # 💜 Remove the alert
            if pokemon.isdigit():
                removed_count = await remove_market_alert(bot, user_id, pokemon)
                if removed_count > 0:
                    removed_alerts.append((target_name.title(), pokemon))
            else:
                removed_count = await remove_market_alert(
                    bot, user_id, target_name.lower()
                )
                if removed_count > 0:
                    removed_alerts.append((target_name.title(), dex_number))

            await load_market_alert_cache(bot)
            status = await refund_market_alert(bot=bot, user=user)
            status_message = status["message"]
    except Exception as e:
        await loader.stop(content=f"❌ Failed to remove alert: {e}")
        espeon_log("critical", f"Failed to remove alert: {e}", source="MarketAlert")
        return

    # 💜 Build final embed
    status_line = status_message
    member_line = f"- Member: {user.mention}"

    if removed_alerts:
        if len(removed_alerts) == 1:
            name, dex = removed_alerts[0]
            removed_line = f"- Removed Pokémon: {name} #{dex}"
        else:
            removed_line = (
                f"{Espeon_Emoji.purple_broom} Removed Pokémon(s):\n"
                + "\n".join([f"> - {name} #{dex}" for name, dex in removed_alerts])
            )

        user_embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_hearts_one} Market Alert Removed",
            description=f"{status_line}\n{member_line}\n{removed_line}",
        )
        user_embed = await design_embed(
            embed=user_embed,
            user=user,
            footer_text=footer_text,
            pokemon_name=name,
        )
    else:
        user_embed = discord.Embed(
            title="❌ No Alert Found",
            description=f"No active alert found for **{pokemon.title()}**.",
            color=0xFF99FF,
        )

    # 💜 Log embed
    clan_staff = interaction.guild.get_role(STRAYMONS__ROLES.clan_staff)
    is_staff = clan_staff in user.roles if clan_staff else False
    log_channel = get_log_channel(bot=bot)

    if removed_alerts and log_channel:
        log_description = f"{Espeon_Emoji.purple_broom} Alert(s) Removed\n".join(
            [f"> - {name} #{dex}" for name, dex in removed_alerts]
        )
        log_embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_hearts_one} Market Alert Removed",
            description=f"{status_message}\n- {Espeon_Emoji.purple_star} Member: {user.mention}\n- {Espeon_Emoji.purple_plushie} Pokemon:\n{log_description}",
            color=0xFF99FF,
            timestamp=datetime.now(),
        )
        log_embed = await design_embed(embed=log_embed, user=user)

    # 💜 Stop loader and show final embed
    await loader.stop(content=f"{user.mention}", embed=user_embed)
    espeon_log(
        "sent",
        f"Removed {len(removed_alerts)} market alert(s) for user {user_id}",
        source="MarketAlert",
    )

    if log_channel and removed_alerts:
        await log_channel.send(embed=log_embed)
