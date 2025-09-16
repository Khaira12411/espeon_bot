import discord
from utils.loggers.espeon_log import espeon_log, EspeonContext
from discord.ext import commands
from discord import app_commands


# 💜────────────────────────────────────────────
#   🟣 Autocomplete for WB Sub Removal
# 💜────────────────────────────────────────────
async def wb_sub_autocomplete(
    interaction: discord.Interaction,
    current: str,
):
    """
    Suggest WB subscriptions the user already has.
    Autocomplete will return boss+variant+mode combos.
    """
    user_id = interaction.user.id
    rows = await fetch_all_user_wb_pings(bot=interaction.client, user_id=user_id)

    choices = []
    for row in rows:
        boss = row["boss_name"].title()
        variant = row["variant"].title()
        mode = row["mode"].title()
        label = f"{boss} ({variant}, {mode})"
        if current.lower() in label.lower():
            choices.append(
                app_commands.Choice(name=label, value=f"{boss}|{variant}|{mode}")
            )

    return choices[:25]  # Discord limit


# 💜────────────────────────────────────────────
#   🟣 Upsert WB Ping Subscription
# 💜────────────────────────────────────────────
async def upsert_user_wb_ping(
    bot,
    user_id: int,
    user_name: str,
    variant: str,
    boss_name: str,
    mode: str,
    channel_id: int = None,
) -> dict | None:
    query = """
    INSERT INTO user_wb_ping (user_id, user_name, variant, boss_name, mode, channel_id)
    VALUES ($1, $2, $3, lower($4), $5, $6)
    ON CONFLICT (user_id, boss_name)
    DO UPDATE SET
      user_name  = EXCLUDED.user_name,
      variant    = EXCLUDED.variant,
      mode       = EXCLUDED.mode,
      channel_id = EXCLUDED.channel_id,
      created_at = NOW()
    RETURNING *
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                query, user_id, user_name, variant, boss_name, mode, channel_id
            )
        return dict(row) if row else None
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to upsert wb_ping row for {user_id}/{boss_name}: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return None


# 💜────────────────────────────────────────────
#   🟣 Update WB Sub (mode + variant only)
# 💜────────────────────────────────────────────
async def update_user_wb_ping_variant_mode(
    bot,
    user_id: int,
    boss_name: str,
    new_variant: str,
    new_mode: str,
) -> bool:
    query = """
    UPDATE user_wb_ping
    SET variant = $1, mode = $2
    WHERE user_id = $3 AND boss_name = lower($4)
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                query, new_variant, new_mode, user_id, boss_name
            )
        return result[-1] != "0"
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to update wb_ping variant/mode for {user_id}/{boss_name}: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return False


# 💜────────────────────────────────────────────
#   🟣 Remove WB Ping (per Boss)
# 💜────────────────────────────────────────────
async def remove_user_wb_ping(bot, user_id: int, boss_name: str) -> bool:
    query = "DELETE FROM user_wb_ping WHERE user_id = $1 AND boss_name = lower($2)"
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(query, user_id, boss_name)
        return result[-1] != "0"
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to remove wb_ping row for {user_id}/{boss_name}: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return False


# 💜────────────────────────────────────────────
#   🟣 Remove All WB Pings (per User)
# 💜────────────────────────────────────────────
async def remove_all_user_wb_pings(bot, user_id: int) -> bool:
    query = "DELETE FROM user_wb_ping WHERE user_id = $1"
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(query, user_id)
        return result[-1] != "0"
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to remove all wb_ping rows for {user_id}: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return False


# 💜────────────────────────────────────────────
#   🟣 Fetch WB Ping Row (per Boss)
# 💜────────────────────────────────────────────
async def fetch_user_wb_ping(bot, user_id: int, boss_name: str) -> dict | None:
    query = "SELECT * FROM user_wb_ping WHERE user_id = $1 AND boss_name = lower($2)"
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, boss_name)
        return dict(row) if row else None
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to fetch wb_ping row for {user_id}/{boss_name}: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return None


# 💜────────────────────────────────────────────
#   🟣 Fetch All WB Pings (per User)
# 💜────────────────────────────────────────────
async def fetch_all_user_wb_pings(bot, user_id: int) -> list[dict]:
    query = "SELECT * FROM user_wb_ping WHERE user_id = $1 ORDER BY created_at DESC"
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
        return [dict(row) for row in rows]
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to fetch all wb_ping rows for {user_id}: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return []


# 💜────────────────────────────────────────────
#   🟣 Fetch All WB Pings (Global)
# 💜────────────────────────────────────────────
async def fetch_all_wb_pings(bot) -> list[dict]:
    query = "SELECT * FROM user_wb_ping ORDER BY created_at DESC"
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(query)

        espeon_log(
            tag="db",
            message=f"📥 Fetched {len(rows)} rows from DB",
            context=EspeonContext.STRAYMONS,
        )
        return [dict(row) for row in rows]

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to fetch all wb_ping rows: {e}",
            exc=e,
            context=EspeonContext.STRAYMONS,
        )
        return []
