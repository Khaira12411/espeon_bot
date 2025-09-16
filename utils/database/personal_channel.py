from utils.loggers.espeon_log import espeon_log, EspeonContext
import discord


# 💜────────────────────────────────────────────
#       🟣 Personal Channel Fetcher 🟣
# 💜────────────────────────────────────────────
async def get_registered_personal_channel(
    bot: discord.Client, user_id: int
) -> int | None:
    """
    Fetch the registered personal channel ID for a given user from DB.
    Returns None if not found or if an error occurs.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT channel_id FROM personal_channels WHERE user_id = $1",
                user_id,
            )
            channel_id = row["channel_id"] if row else None

            espeon_log(
                tag="db",
                message=f"💜 Fetched personal channel for user {user_id}: {channel_id}",
                label="🦩 PERSONAL CHANNEL",
                context=EspeonContext.STRAYMONS,
            )
            return channel_id

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch personal channel for user {user_id}: {e}",
            exc=e,
            label="🦩 PERSONAL CHANNEL",
            context=EspeonContext.STRAYMONS,
        )
        return None
