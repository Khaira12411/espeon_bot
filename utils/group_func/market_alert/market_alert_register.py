# 🟣────────────────────────────────────────────
#           💜 Market Alert Auto-Register + Embed 💜
# 🟣────────────────────────────────────────────
from datetime import datetime
from typing import List, Optional

import discord
from discord.ext import commands

from config.aesthetic import *
from config.current_setup import STAFF_SERVER_GUILD_ID, STRAYMONS_GUILD_ID
from config.straymons_constants import *
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.get_log_channel import get_log_channel
from utils.visuals.embeds.visual_helpers import design_embed

ROLE_COUNTER = {
    STRAYMONS__ROLES.top_catcher: 1,
    STRAYMONS__ROLES.floriane: 3,
    STRAYMONS__ROLES.server_booster: 1,
    STRAYMONS__ROLES.vip: 2,
    STRAYMONS__ROLES.bloomia: 2,
    STRAYMONS__ROLES.seedlet: 1,
    STRAYMONS__ROLES.clan_bank: 1,
}


async def market_alert_register_func(
    bot: commands.Bot, interaction: discord.Interaction
):
    """
    Register a user for market alerts safely.
    Auto-grant unlimited alerts for anyone in the staff guild.
    Exit early if user has no eligible roles.
    """
    user = interaction.user
    user_id = user.id
    user_name = str(user)

    log_channel = get_log_channel(bot=bot)

    # -------------------- ELIGIBLE ROLES CHECK --------------------
    eligible_roles = [role.id for role in user.roles if role.id in ROLE_COUNTER]
    is_staff = any(role.id == STRAYMONS__ROLES.clan_staff for role in user.roles)

    if not is_staff and not eligible_roles:
        role_list_text = ", ".join(
            [f"<@&{role_id}>" for role_id in ROLE_COUNTER.keys()]
        )
        embed_fail = discord.Embed(
            title="❌ Cannot Register",
            description=(
                "You must have at least one eligible role to register for market alerts. 🌸\n\n"
                f"Roles that grant alerts include: {role_list_text}"
            ),
            color=0xFF99FF,
        )
        await interaction.response.send_message(embed=embed_fail, ephemeral=True)

        # Log attempt
        espeon_log(
            tag="warn",
            message=f"User {user_id} tried to register without staff or eligible roles.",
            context=EspeonContext.STRAYMONS,
        )
        return 0

    # -------------------- STAFF GUILD AUTO UNLIMITED --------------------
    if interaction.guild.id == STAFF_SERVER_GUILD_ID:
        total_alerts = 50
        alerts_used = 0

        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, total_alerts FROM market_alert_counter WHERE user_id = $1",
                user_id,
            )
            if not row:
                await conn.execute(
                    """
                    INSERT INTO market_alert_counter
                    (user_id, user_name, roles, server_boost_count, total_alerts, alerts_used)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id,
                    user_name,
                    [r.id for r in user.roles],
                    getattr(user, "premium_subscription_count", 0),
                    total_alerts,
                    alerts_used,
                )
            else:
                await conn.execute(
                    """
                    UPDATE market_alert_counter
                    SET roles = $1, server_boost_count = $2, total_alerts = $3
                    WHERE user_id = $4
                    """,
                    [r.id for r in user.roles],
                    getattr(user, "premium_subscription_count", 0),
                    total_alerts,
                    user_id,
                )

        embed_user = discord.Embed(
            title="💜 Market Alerts (Staff Guild Magic!)",
            description="✨ You can use **as many market alerts as you want**! 🌷",
            color=0xFF99FF,
        )
        embed_user.set_footer(
            text="Staff guild members have unlimited market alerts 💜"
        )
        await interaction.response.send_message(embed=embed_user, ephemeral=True)

        embed_log = discord.Embed(
            title="💜 Market Alert Registration (Staff Guild)",
            description=f"User {user_name} connected in staff guild. Total alerts = unlimited.",
            color=0xFF99FF,
        )
        await log_channel.send(embed=embed_log)
        return total_alerts

    # -------------------- REGULAR USERS --------------------
    server_boost_count = getattr(user, "premium_subscription_count", 0)
    total_alerts = (
        sum(ROLE_COUNTER.get(role_id, 0) for role_id in eligible_roles)
        + server_boost_count
    )
    total_alerts = min(total_alerts, 10)
    alerts_used = 0

    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, total_alerts FROM market_alert_counter WHERE user_id = $1",
            user_id,
        )
        if not row:
            await conn.execute(
                """
                INSERT INTO market_alert_counter
                (user_id, user_name, roles, server_boost_count, total_alerts, alerts_used)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_id,
                user_name,
                eligible_roles,
                server_boost_count,
                total_alerts,
                alerts_used,
            )
        else:
            await conn.execute(
                """
                UPDATE market_alert_counter
                SET total_alerts = $1, roles = $2, server_boost_count = $3
                WHERE user_id = $4
                """,
                total_alerts,
                eligible_roles,
                server_boost_count,
                user_id,
            )

    # Build role breakdown
    role_breakdown_lines = [
        f"> - {interaction.guild.get_role(role_id).mention}: +{ROLE_COUNTER.get(role_id, 0)}"
        for role_id in eligible_roles
        if interaction.guild.get_role(role_id)
    ]
    if server_boost_count > 0:
        role_breakdown_lines.append(f"> - Server Boosts: +{server_boost_count}")

    role_breakdown_text = "\n".join(role_breakdown_lines)

    embed_user = discord.Embed(
        title=f"{Espeon_Emoji.purple_hearts_one} Market Alerts Registered!",
        description=(
            f"✨ You have **{total_alerts} free market alerts** available! 🌸\n\n"
            f"**{Espeon_Emoji.purple_ribbon} Alert Breakdown:**\n{role_breakdown_text}"
        ),
        color=0xFF99FF,
    )
    embed_user.set_footer(
        text="Don't forget to add your alerts via /market-alert add 💜"
    )
    await interaction.response.send_message(embed=embed_user, ephemeral=True)

    embed_log = discord.Embed(
        title=f"{Espeon_Emoji.purple_hearts_one} Market Alert Registration",
        description=(
            f"- Member: {user.mention}\n"
            f"- Total Alerts: {total_alerts}\n\n"
            f"**{Espeon_Emoji.purple_ribbon} Alert Breakdown:**\n{role_breakdown_text}"
        ),
        color=0xFF99FF,
        timestamp=datetime.now(),
    )
    embed_log = design_embed(embed=embed_log, user=user)
    await log_channel.send(embed=embed_log)

    return total_alerts
