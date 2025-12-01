from datetime import datetime

import discord

from utils.database.webhook_url_db import upsert_webhook_url
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.cache.cache_list import webhook_url_cache

async def create_webhook_func(
    bot, channel: discord.TextChannel, name: str
) -> str | None:
    try:

        avatar_bytes = await bot.user.avatar.read()
        webhook = await channel.create_webhook(name=name, avatar=avatar_bytes)
        espeon_log(
            "info",
            f"Webhook '{name}' created in channel '{channel.name}' (ID: {channel.id})",
        )
        # Store the webhook URL in the database
        await upsert_webhook_url(bot, channel, webhook.url)

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to create webhook in channel '{channel.name}': {e}",
        )
    return webhook.url if webhook else None


async def send_webhook(
    bot: discord.Client,
    channel: discord.TextChannel,
    content: str = None,
    embed: discord.Embed = None,
):
    channel_id = channel.id
    webhook_url_row = webhook_url_cache.get(channel_id)
    if not webhook_url_row:
        channel_name = channel.name
        if "snipe" in channel_name.lower():
            webhook_name = "Espeon Market Snipe 🌷"
        elif "clan" in channel_name.lower():
            webhook_name = "Espeon Clan Event Log 🌸"
        elif "shop" in channel_name.lower():
            webhook_name = "Espeon Shop Updates 🌺"
        else:
            webhook_name = f"Espeon Webhook {channel_name}"
        webhook_url = await create_webhook_func(bot, channel, webhook_name)
        if not webhook_url:
            espeon_log(
                tag="info",
                message=f"⚠️ Falling back to direct channel send for channel '{channel.name}' (ID: {channel.id}) due to webhook creation failure",
                label="🌐 WEBHOOK SEND",
                context=EspeonContext.ESPEON,
            )
            await channel.send(content=content, embed=embed)
            return
        # Update cache for immediate use
        webhook_url_cache[channel_id] = {
            "channel_name": channel_name,
            "url": webhook_url,
        }
        webhook_url_row = webhook_url_cache[channel_id]

    webhook_url = webhook_url_row["url"]
    if webhook_url:
        webhook = discord.Webhook.from_url(webhook_url, client=bot)
        await webhook.send(content=content, embed=embed, wait=True)
