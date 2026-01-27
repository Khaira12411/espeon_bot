import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log

"""CREATE TABLE webhook_url (
    bot_id BIGINT NOT NULL,
    bot_name TEXT NOT NULL,
    channel_id BIGINT NOT NULL,
    channel_name TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (bot_id, channel_id)
);"""

BOT_ID = 1324718838016770068


async def upsert_webhook_url(
    bot: discord.Client,
    channel: discord.TextChannel,
    webhook_url: str,
):
    bot_name = bot.user.name if bot.user else "Unknown Bot"
    bot_id = BOT_ID
    channel_id = channel.id
    channel_name = channel.name
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO webhook_url (bot_id, bot_name, channel_id, channel_name, url)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (bot_id, channel_id) DO UPDATE
                SET bot_name = EXCLUDED.bot_name,
                    channel_name = EXCLUDED.channel_name,
                    url = EXCLUDED.url;
                """,
                bot_id,
                bot_name,
                channel_id,
                channel_name,
                webhook_url,
            )
            espeon_log(
                tag="db",
                message=f"Upserted webhook URL for bot '{bot_name}' (ID: {bot_id}), channel '{channel_name}' (ID: {channel_id})",
                label="🌐 WEBHOOK URL DB",
                context=EspeonContext.ESPEON,
            )
            # Update the cache as well
            from utils.cache.webhook_url_cache import upsert_webhook_url_in_cache

            upsert_webhook_url_in_cache(channel, webhook_url)
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to upsert webhook URL for bot '{bot_name}' (ID: {bot_id}), channel '{channel_name}' (ID: {channel_id}): {e}",
            exc=e,
            label="🌐 WEBHOOK URL DB",
            context=EspeonContext.ESPEON,
        )


async def fetch_all_webhook_urls(bot: discord.Client) -> dict[int, dict[str, str]]:
    bot_id = BOT_ID
    webhook_url = {}
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT channel_id, channel_name, url FROM webhook_url WHERE bot_id = $1;",
                bot_id,
            )
            for row in rows:
                webhook_url[row["channel_id"]] = {
                    "channel_name": row["channel_name"],
                    "url": row["url"],
                }
            espeon_log(
                tag="db",
                message=f"Fetched {len(webhook_url)} webhook URLs for bot_id {bot_id} from database",
                label="🌐 WEBHOOK URL DB",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch webhook URLs for bot_id {bot_id}: {e}",
            exc=e,
            label="🌐 WEBHOOK URL DB",
            context=EspeonContext.ESPEON,
        )
    return webhook_url


async def remove_webhook_url(bot: discord.Client, channel: discord.TextChannel):
    bot_id = BOT_ID
    channel_id = channel.id
    channel_name = channel.name
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM webhook_url WHERE bot_id = $1 AND channel_id = $2;",
                bot_id,
                channel_id,
            )
            espeon_log(
                tag="db",
                message=f"Removed webhook URL for bot_id '{bot_id}', channel '{channel_name}' (ID: {channel_id})",
                label="🌐 WEBHOOK URL DB",
                context=EspeonContext.ESPEON,
            )
            # Update the cache as well
            from utils.cache.webhook_url_cache import remove_webhook_url_from_cache

            remove_webhook_url_from_cache(channel)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove webhook URL for bot_id '{bot_id}', channel '{channel_name}' (ID: {channel_id}): {e}",
            exc=e,
            label="🌐 WEBHOOK URL DB",
            context=EspeonContext.ESPEON,
        )
