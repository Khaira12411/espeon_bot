from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from config.straymons_constants import *
from utils.loggers.espeon_log import EspeonContext, espeon_log

MAX_ALERTS = 10

ROLE_COUNTER = {
    STRAYMONS__ROLES.top_catcher: 1,
    STRAYMONS__ROLES.floriane: 3,
    STRAYMONS__ROLES.server_booster: 1,
    STRAYMONS__ROLES.vip: 2,
    STRAYMONS__ROLES.bloomia: 2,
    STRAYMONS__ROLES.seedlet: 1,
}


# 💾 Upsert user
async def upsert_user(
    bot,
    user_id: int,
    user_name: str,
    roles: Optional[List[str]] = None,
    server_boost_count: int = 0,
    total_alerts: int = 0,
):
    total_alerts = min(total_alerts, MAX_ALERTS)
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO market_alert_counter (user_id, user_name, roles, server_boost_count, total_alerts)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id)
            DO UPDATE SET
                user_name = $2,
                roles = $3,
                server_boost_count = $4,
                total_alerts = LEAST($5, 10);
            """,
            user_id,
            user_name,
            roles or [],
            server_boost_count,
            total_alerts,
        )


# 📊 Get total alerts for a user
async def get_total_alerts(bot, user_id: int) -> int:
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT total_alerts FROM market_alert_counter WHERE user_id = $1", user_id
        )
        return row["total_alerts"] if row else 0


# 📊 Market Alert Status
CLAN_STAFF_ROLE_ID = (
    STRAYMONS__ROLES.clan_staff
)  # replace with actual clan staff role ID


# 📊 Market Alert Status with clan staff bypass & table sync


# ➕ Increment alerts_used (use one alert)
async def use_market_alert(bot, user: discord.Member):
    """
    Increment alerts_used for a user if not blocked.
    Returns updated status dict.
    """
    user_id = user.id
    status = await get_market_alert_status(bot, user)

    if status["block"]:
        return status  # Can't increment, already maxed

    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE market_alert_counter
            SET alerts_used = alerts_used + 1
            WHERE user_id = $1
            """,
            user_id,
        )

    return await get_market_alert_status(bot, user)


# ➖ Decrement alerts_used (refund one alert)
async def refund_market_alert(bot, user: discord.Member):
    """
    Decrement alerts_used for a user (never below 0).
    Returns updated status dict.
    """
    user_id = user.id
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE market_alert_counter
            SET alerts_used = GREATEST(alerts_used - 1, 0)
            WHERE user_id = $1
            """,
            user_id,
        )

    return await get_market_alert_status(bot, user)


# ➖ Deduct alerts when a role is lost
async def deduct_alerts_for_role_loss(bot, user: discord.Member, role_id: int):
    clan_staff_role = user.guild.get_role(STRAYMONS__ROLES.clan_staff)
    if clan_staff_role in user.roles:
        return

    user_id = user.id
    alerts_to_deduct = ROLE_COUNTER.get(role_id, 0)
    if alerts_to_deduct == 0:
        espeon_log(
            tag="db",
            message=f"Role {role_id} has no alert value, skipping {user}.",
            context=EspeonContext.STRAYMONS,
        )
        return

    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE market_alert_counter
            SET total_alerts = GREATEST(total_alerts - $2, 0),
                roles = array_remove(roles, $3)
            WHERE user_id = $1
            RETURNING total_alerts, alerts_used
            """,
            user_id,
            alerts_to_deduct,
            str(role_id),
        )

        if not row:
            espeon_log(
                tag="db",
                message=f"User {user} not found in market_alert_counter.",
                context=EspeonContext.STRAYMONS,
            )
            return

        # ✅ Cleanup if alerts_used is higher than new total
        if row["alerts_used"] > row["total_alerts"]:
            await remove_recent_market_alerts(bot, user, role_id=role_id)
            espeon_log(
                tag="db",
                message=f"Cleanup triggered for {user} ({user_id}) after role loss. "
                f"Total: {row['total_alerts']} | Used: {row['alerts_used']}",
                context=EspeonContext.STRAYMONS,
            )
        else:
            espeon_log(
                tag="db",
                message=f"Alerts deducted for {user} ({user_id}). Now has {row['total_alerts']} total.",
                context=EspeonContext.STRAYMONS,
            )


# ➖ Deduct alerts when a boost is lost
async def deduct_alerts_for_boost_loss(bot, user_id: int):
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE market_alert_counter
            SET total_alerts = GREATEST(total_alerts - 1, 0),
                server_boost_count = GREATEST(server_boost_count - 1, 0)
            WHERE user_id = $1
            RETURNING total_alerts, alerts_used
            """,
            user_id,
        )

        if not row:
            return "User not found."

        if row["alerts_used"] > row["total_alerts"]:
            await remove_recent_market_alerts(bot, user_id)
            espeon_log(
                tag="db",
                message=f"Cleanup triggered for user {user_id} after boost loss",
                context=EspeonContext.STRAYMONS,
            )
            return "Boost removed, cleanup triggered."

        return f"Boost removed, user now has {row['total_alerts']}."


# ➖ Remove recent market alerts and update alerts_used
async def remove_recent_market_alerts(
    bot: commands.Bot, user: discord.Member, role_id: int | None = None
):
    role_name = None
    if role_id:
        role = user.guild.get_role(role_id)
        role_name = role.name if role else f"Role {role_id}"

    async with bot.pg_pool.acquire() as conn:
        counters = await conn.fetchrow(
            """
            SELECT total_alerts, alerts_used
            FROM market_alert_counter
            WHERE user_id = $1
            """,
            user.id,
        )

        if not counters:
            return None

        excess = counters["alerts_used"] - counters["total_alerts"]
        if excess <= 0:
            return None

        rows = await conn.fetch(
            """
            SELECT id, pokemon, dex_number, max_price, channel_id
            FROM market_alerts
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user.id,
            excess,
        )

        if not rows:
            return None

        alert_ids = [r["id"] for r in rows]
        await conn.execute(
            "DELETE FROM market_alerts WHERE id = ANY($1::int[])", alert_ids
        )

        updated_row = await conn.fetchrow(
            """
            UPDATE market_alert_counter
            SET alerts_used = GREATEST(alerts_used - $2, 0)
            WHERE user_id = $1
            RETURNING total_alerts, alerts_used
            """,
            user.id,
            len(rows),
        )

    reason = f"Lost role: **{role_name}**" if role_name else "Lost server boost"

    # Try DM
    try:
        user_embed = discord.Embed(
            title="⏬ Alerts Removed",
            description=f"{len(rows)} of your market alert(s) were removed due to **{reason}**.",
            color=0x00FFFF,
        )
        for r in rows[:25]:
            user_embed.add_field(
                name=f"{r['pokemon']} (Dex {r['dex_number']})",
                value=f"Max Price: {r['max_price']} | Channel: <#{r['channel_id']}>",
                inline=False,
            )
        if len(rows) > 25:
            user_embed.set_footer(
                text=f"And {len(rows) - 25} more alerts were removed..."
            )
        if updated_row:
            user_embed.add_field(
                name="Your New Totals",
                value=f"📊 **Total Allowed**: {updated_row['total_alerts']}\n"
                f"📌 **Currently Used**: {updated_row['alerts_used']}",
                inline=False,
            )
        await user.send(embed=user_embed)
    except Exception:
        espeon_log(
            tag="warn",
            message=f"Could not DM {user}",
            context=EspeonContext.STRAYMONS,
        )

    # Send log to server
    log_channel: discord.TextChannel = bot.get_channel(
        STRAYMONS__TEXT_CHANNELS.server_logs
    )
    if log_channel:
        log_embed = discord.Embed(
            title="🔔 Market Alerts Removed",
            description=f"{len(rows)} alert(s) removed for {user.mention} (`{user.id}`)\nReason: **{reason}**",
            color=0x8A2BE2,
        )
        log_embed.set_thumbnail(url=user.display_avatar.url)
        for r in rows[:5]:
            log_embed.add_field(
                name=f"{r['pokemon']} (Dex {r['dex_number']})",
                value=f"Max Price: {r['max_price']} | Channel: <#{r['channel_id']}>",
                inline=False,
            )
        if len(rows) > 5:
            log_embed.set_footer(text=f"+ {len(rows) - 5} more alerts removed...")
        if updated_row:
            log_embed.add_field(
                name="New Totals",
                value=f"📊 **Total Allowed**: {updated_row['total_alerts']}\n"
                f"📌 **Currently Used**: {updated_row['alerts_used']}",
                inline=False,
            )
        await log_channel.send(embed=log_embed)


async def get_market_alert_status(bot, user: discord.Member):
    """
    Fetch total and used market alerts for a user.
    - Registers user in market_alert_counter if missing (roles are always saved as int[]).
    - Clan staff: total_alerts = number of alerts currently in market_alerts table,
      but their total_alerts in DB is NOT overwritten.
    - Returns dict with totals, left, block flag, and message.
    """
    user_id = user.id
    user_roles_ids = [r.id for r in user.roles]
    is_clan_staff = CLAN_STAFF_ROLE_ID in user_roles_ids

    async with bot.pg_pool.acquire() as conn:
        # Count entries in market_alerts table
        market_alert_rows = await conn.fetchval(
            "SELECT COUNT(*) FROM market_alerts WHERE user_id = $1", user_id
        )

        # Fetch existing row
        row = await conn.fetchrow(
            "SELECT total_alerts, alerts_used FROM market_alert_counter WHERE user_id = $1",
            user_id,
        )

        # If no row exists, insert one
        if not row:
            total_alerts = market_alert_rows if is_clan_staff else 0
            alerts_used = market_alert_rows if is_clan_staff else 0

            await conn.execute(
                """
                INSERT INTO market_alert_counter
                (user_id, user_name, roles, server_boost_count, total_alerts, alerts_used)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_id,
                str(user),
                user_roles_ids,  # stored as int[]
                getattr(user, "premium_subscription_count", 0),
                total_alerts,
                alerts_used,
            )
        else:
            total_alerts = row["total_alerts"]
            alerts_used = row["alerts_used"]

            # Sync total alerts for normal users if table has more alerts than DB
            if not is_clan_staff and market_alert_rows > total_alerts:
                total_alerts = market_alert_rows
                await conn.execute(
                    "UPDATE market_alert_counter SET total_alerts = $1 WHERE user_id = $2",
                    total_alerts,
                    user_id,
                )

            # Always update roles in DB to reflect current user roles
            await conn.execute(
                "UPDATE market_alert_counter SET roles = $1 WHERE user_id = $2",
                user_roles_ids,
                user_id,
            )

            # For staff: ensure alerts_used reflects current rows in market_alerts
            if is_clan_staff:
                alerts_used = market_alert_rows
                await conn.execute(
                    "UPDATE market_alert_counter SET alerts_used = $1 WHERE user_id = $2",
                    alerts_used,
                    user_id,
                )

    # Compute remaining alerts
    alerts_left = max(total_alerts - alerts_used, 0)

    # Build message
    if total_alerts == 0:
        message = "❌ You don’t have any free market alerts yet. 🍰"
        block = True
    elif alerts_used >= total_alerts:
        message = f"⚠️ You’ve used all {total_alerts} of your free market alerts. 🪻"
        block = True
    else:
        plural = "alert" if total_alerts == 1 else "alerts"
        message = (
            f"✨ You’ve used {alerts_used} of your {total_alerts} free market {plural}. "
            f"({alerts_left} left!) 🌸"
        )
        block = False

    # Staff always bypass
    if is_clan_staff:
        block = False
        message = (
            f"✨ Clan staff magic! You currently have {alerts_used} alert(s). "
            "You can always add more! 🌷"
        )

    return {
        "total_alerts": total_alerts,
        "alerts_used": alerts_used,
        "alerts_left": alerts_left,
        "block": block,
        "message": message,
    }
