import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log

"""CREATE TABLE webhook_url (
    channel_id BIGINT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    url TEXT NOT NULL
);"""


async def upsert_webhook_url(
    bot: discord.Client, channel: discord.TextChannel, webhook_url: str
):
    channel_id = channel.id
    channel_name = channel.name
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO webhook_url (channel_id, channel_name, url)
                VALUES ($1, $2, $3)
                ON CONFLICT (channel_id) DO UPDATE
                SET channel_name = EXCLUDED.channel_name,
                    url = EXCLUDED.url;
                """,
                channel_id,
                channel_name,
                webhook_url,
            )
            espeon_log(
                tag="db",
                message=f"Upserted webhook URL for channel '{channel_name}' (ID: {channel_id})",
                label="🌐 WEBHOOK URL DB",
                context=EspeonContext.ESPEON,
            )
            # Update the cache as well
            from utils.cache.webhook_url_cache import upsert_webhook_url_in_cache

            upsert_webhook_url_in_cache(channel, webhook_url)
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to upsert webhook URL for channel '{channel_name}' (ID: {channel_id}): {e}",
            exc=e,
            label="🌐 WEBHOOK URL DB",
            context=EspeonContext.ESPEON,
        )


async def fetch_all_webhook_urls(bot: discord.Client) -> dict[int, str]:
    webhook_list = []
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT channel_id, url, channel_name FROM webhook_url;"
            )
            for row in rows:
                webhook_list.append(
                    (row["channel_id"], row["url"], row["channel_name"])
                )
            espeon_log(
                tag="db",
                message=f"Fetched {len(webhook_list)} webhook URLs from database",
                label="🌐 WEBHOOK URL DB",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch webhook URLs: {e}",
            exc=e,
            label="🌐 WEBHOOK URL DB",
            context=EspeonContext.ESPEON,
        )
    return webhook_list


async def remove_webhook_url(bot: discord.Client, channel: discord.TextChannel):
    channel_id = channel.id
    channel_name = channel.name
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM webhook_url WHERE channel_id = $1;",
                channel_id,
            )
            espeon_log(
                tag="db",
                message=f"Removed webhook URL for channel '{channel_name}' (ID: {channel_id})",
                label="🌐 WEBHOOK URL DB",
                context=EspeonContext.ESPEON,
            )
            # Update the cache as well
            from utils.cache.webhook_url_cache import remove_webhook_url_from_cache

            remove_webhook_url_from_cache(channel)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove webhook URL for channel '{channel_name}' (ID: {channel_id}): {e}",
            exc=e,
            label="🌐 WEBHOOK URL DB",
            context=EspeonContext.ESPEON,
        )
