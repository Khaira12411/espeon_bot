# 🟣────────────────────────────────────────────
#           💜 Market Alert Auto-Register + Embed 💜
# 🟣────────────────────────────────────────────
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from config.straymons_constants import *
from utils.loggers.espeon_log import espeon_log

ROLE_COUNTER = {
    STRAYMONS__ROLES.top_catcher: 1,
    STRAYMONS__ROLES.floriane: 3,
    STRAYMONS__ROLES.server_booster: 1,
    STRAYMONS__ROLES.vip: 2,
    STRAYMONS__ROLES.bloomia: 2,
    STRAYMONS__ROLES.seedlet: 1,
}


async def market_alert_register_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    Register a user for market alerts.
    - Staff bypass: unlimited alerts, still creates/updates DB row, but does not overwrite staff total every run.
    - Regular users: must have at least one eligible role from ROLE_COUNTER.
    Always stores roles[] in DB.
    Sends ephemeral embed to user and log embed to server logs.
    Returns total alerts assigned.
    """
    user = interaction.user
    user_id = user.id
    user_name = str(user)
    log_channel = interaction.guild.get_channel(STRAYMONS__TEXT_CHANNELS.server_logs)

    async with bot.pg_pool.acquire() as conn:
        # 🔹 Check if row exists
        row = await conn.fetchrow(
            "SELECT user_id, total_alerts FROM market_alert_counter WHERE user_id = $1",
            user_id,
        )

        # 🌟 Staff bypass
        is_staff = any(role.id == STRAYMONS__ROLES.clan_staff for role in user.roles)
        user_roles = [r.id for r in user.roles]
        server_boost_count = getattr(user, "premium_subscription_count", 0)

        if is_staff:
            total_alerts = 999  # Arbitrary large number for staff
            alerts_used = 0

            if not row:
                # First time staff register → create row
                await conn.execute(
                    """
                    INSERT INTO market_alert_counter
                    (user_id, user_name, roles, server_boost_count, total_alerts, alerts_used)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id,
                    user_name,
                    user_roles,  # 🔹 Always store roles[] as int[]
                    server_boost_count,
                    total_alerts,
                    alerts_used,
                )
            else:
                # Update roles + boost count, but don't overwrite staff total
                await conn.execute(
                    """
                    UPDATE market_alert_counter
                    SET roles = $1, server_boost_count = $2
                    WHERE user_id = $3
                    """,
                    user_roles,
                    server_boost_count,
                    user_id,
                )

            # Ephemeral user embed
            embed_user = discord.Embed(
                title="💜 Market Alerts (Staff Magic!)",
                description="✨ You can use **as many market alerts as you want**! 🌷",
                color=0xFF99FF,
            )
            embed_user.set_footer(text="Staff members have unlimited market alerts 💜")
            await interaction.response.send_message(embed=embed_user, ephemeral=True)

            # Log embed
            embed_log = discord.Embed(
                title="💜 Market Alert Registration (Staff)",
                description=f"Staff {user_name} connected. Total alerts = unlimited.",
                color=0xFF99FF,
            )
            await log_channel.send(embed=embed_log)
            return total_alerts

        # ✅ Regular users: calculate from roles
        roles = [role.id for role in user.roles if role.id in ROLE_COUNTER]
        if not roles:
            embed_fail = discord.Embed(
                title="❌ Cannot Register",
                description="You must have at least one eligible role to register for market alerts. 🌸",
                color=0xFF99FF,
            )
            embed_fail.set_footer(
                text="Roles that grant alerts include: "
                + ", ".join([f"<@&{role_id}>" for role_id in ROLE_COUNTER.keys()])
            )
            await interaction.response.send_message(embed=embed_fail, ephemeral=True)
            return 0

        total_alerts = sum(ROLE_COUNTER.get(role_id, 0) for role_id in roles)
        total_alerts += server_boost_count

        from utils.group_func.market_alert.db_func.market_alert_db_func import (
            MAX_ALERTS,
        )

        total_alerts = min(total_alerts, MAX_ALERTS)
        alerts_used = 0

        if not row:
            await conn.execute(
                """
                INSERT INTO market_alert_counter
                (user_id, user_name, roles, server_boost_count, total_alerts, alerts_used)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_id,
                user_name,
                roles,
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
                roles,
                server_boost_count,
                user_id,
            )

        # 🔹 Ephemeral user embed
        embed_user = discord.Embed(
            title="💜 Market Alerts Registered!",
            description=f"✨ You have **{total_alerts} free market alerts** available! 🌸",
            color=0xFF99FF,
        )
        embed_user.set_footer(
            text="You'll be notified when a Pokémon matches your alert 💜"
        )
        await interaction.response.send_message(embed=embed_user, ephemeral=True)

        # 🔹 Log embed
        embed_log = discord.Embed(
            title="💜 Market Alert Registration",
            description=f"User {user_name} registered with **{total_alerts} alerts**.",
            color=0xFF99FF,
        )
        await log_channel.send(embed=embed_log)

        return total_alerts
