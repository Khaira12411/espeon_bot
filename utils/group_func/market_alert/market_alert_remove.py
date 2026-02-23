# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain: Remove 💜
# ─────────────────────────────────────────────

from datetime import datetime

import discord

from config.aesthetic import *
from utils.database.server_shop import format_item_name
from utils.essentials.loader import pretty_defer
from utils.function.webhook import send_webhook
from utils.group_func.market_alert.db_func.market_alert_counter import *
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    fetch_user_alerts,
    remove_all_market_alerts,
    remove_market_alert,
)
from utils.group_func.market_alert.parsers import (
    parse_special_mega_input,
    resolve_pokemon_input,
)
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import espeon_log
from utils.visuals.embeds.get_log_channel import get_log_channel
from utils.visuals.embeds.visual_helpers import design_embed


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › Market Alert Remove ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def remove_market_alert_func(bot, interaction: discord.Interaction, pokemon: str):
    """
    Removes a market alert for a user.
    Uses pretty_defer loader: runs full workflow first, then updates loader once with final result.
    """
    from utils.cache.market_alert_cache import remove_alert, remove_all_alerts_from_user

    user = interaction.user
    user_id = user.id
    removed_alerts: list[tuple[str, str]] = []
    footer_text = "💜 You will no longer receive alerts for these Pokemon"

    # 💜 Start loader
    loader = await pretty_defer(
        interaction, content="Processing market alert removal...", ephemeral=False
    )
    user_alerts = await fetch_user_alerts(bot, user_id)

    if not user_alerts:
        await loader.error(content=f"You have no active market alerts.")
        return

    status_message = ""  # 💜 Initialize to empty string

    try:
        # 💜 SEPARATE BRANCH FOR "ALL"
        if pokemon.lower() == "all":
            removed_alerts = [
                (alert["pokemon"].title(), alert["dex_number"]) for alert in user_alerts
            ]

            # 💜 Remove all alerts from DB
            await remove_all_market_alerts(bot, user_id)

            # 💜 Remove all alerts from cache
            remove_all_alerts_from_user(user_id=user_id)

            # 💜 Set status message for "all"
            status_message = "No Alerts Used"

        else:
            # 💜 SINGLE Pokemon LOGIC
            pokemon_title = pokemon.title()
            target_key = pokemon if pokemon.isdigit() else pokemon_title

            # 💜 Determine target_name and dex_number
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

            # 💜 Check if alert exists
            user_alerts = await fetch_user_alerts(bot, user_id)
            exists = any(
                (pokemon.isdigit() and alert["dex_number"] == int(pokemon))
                or (
                    not pokemon.isdigit()
                    and alert["pokemon"].lower() == target_name.lower()
                )
                for alert in user_alerts
            )

            if not exists:
                await loader.error(
                    content=f"No active alert found for **{pokemon_title}**."
                )
                return

            # 💜 Remove alert
            if pokemon.isdigit():
                removed_count = await remove_market_alert(bot, user_id, pokemon)
                if removed_count > 0:
                    removed_alerts.append((target_name.title(), pokemon))
                    alert = next(
                        (a for a in user_alerts if a["dex_number"] == int(pokemon)),
                        None,
                    )
                    if alert:
                        remove_alert(alert["pokemon"], alert["channel_id"], user_id)
            else:
                removed_count = await remove_market_alert(
                    bot, user_id, target_name.lower()
                )
                if removed_count > 0:
                    removed_alerts.append((target_name, display_name))
                    alert = next(
                        (
                            a
                            for a in user_alerts
                            if a["pokemon"].lower() == target_name.lower()
                        ),
                        None,
                    )
                    if alert:
                        remove_alert(alert["pokemon"], alert["channel_id"], user_id)

            # 💜 Refund used alert
            status = await refund_market_alert(bot=bot, user=user)
            status_message = status["message"]

    except Exception as e:
        await loader.error(content=f"Failed to remove alert: {e}")
        espeon_log("critical", f"Failed to remove alert: {e}", source="MarketAlert")
        return

    # 💜 Build final embed
    status_line = status_message
    member_line = f"- Member: {user.mention}"

    if removed_alerts:
        if len(removed_alerts) == 1:
            # Only show emoji and name (display_name)
            display_name = removed_alerts[0][1]  # Only the display_name part
            removed_line = f"- Removed Pokemon: {display_name}"
        else:
            removed_line = (
                f"{Espeon_Emoji.purple_broom} Removed Pokemon(s):\n"
                + "\n".join(
                    [f"> - {display_name}" for _, display_name in removed_alerts]
                )
            )

        pokemon_name_for_embed = removed_alerts[0][0] if removed_alerts else None
        user_embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_hearts_one} Market Alert Removed",
            description=f"{status_line}\n{member_line}\n{removed_line}",
        )
        user_embed = design_embed(
            embed=user_embed,
            user=user,
            footer_text=footer_text,
            pokemon_name=target_name,
        )
    else:
        user_embed = discord.Embed(
            title="❌ No Alert Found",
            description=f"No active alert found for **{pokemon.title()}**.",
            color=0xFF99FF,
        )

    # 💜 Log embed
    log_channel = get_log_channel(bot=bot)
    if removed_alerts and log_channel:
        log_description = "\n".join(
            [f"> - {display_name}" for _, display_name in removed_alerts]
        )
        log_embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_hearts_one} Market Alert Removed",
            description=f"{status_message}\n- {Espeon_Emoji.purple_star} Member: {user.mention}\n- {Espeon_Emoji.purple_plushie} Pokemon:\n{log_description}",
            color=0xFF99FF,
            timestamp=datetime.now(),
        )
        log_embed = design_embed(embed=log_embed, user=user, pokemon_name=target_name)

    # 💜 Stop loader and send
    await loader.success(content="", embed=user_embed)
    espeon_log(
        "sent",
        f"Removed {len(removed_alerts)} market alert(s) for user {user_id}",
        source="MarketAlert",
    )

    if log_channel and removed_alerts:
        await send_webhook(
            bot=bot,
            channel=log_channel,
            embed=log_embed,
        )
