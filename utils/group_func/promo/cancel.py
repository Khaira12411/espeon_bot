from datetime import datetime
import re

import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.clan_promo_db import delete_promo, fetch_active_promo
from utils.essentials.loader import pretty_defer
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

from .add import get_promo_log_settings


async def cancel_promo_func(bot, interaction: discord.Interaction):
    """
    Cancel the active promo in the database.
    """
    log_channel_id, testing_mode, clan_event_log_channel_id = get_promo_log_settings()

    # Defer the interaction
    loader = await pretty_defer(interaction, content="Cancelling active promo...")

    # Check if there is an active promo
    active_promo = await fetch_active_promo(bot)
    if not active_promo:
        await loader.error(
            content="❌ There is no active promo to cancel. Please add a promo first."
        )
        return
    image_url = active_promo.get("image_url")
    emoji = active_promo.get("emoji")
    # Delete the active promo from the database
    await delete_promo(bot)

    # Log the cancellation
    action = "Cancelled" if not testing_mode else "Tested cancelling"
    log_message = f"{action} promo '{active_promo['name']}' with prize '{active_promo['prize']}'."
    espeon_log(
        "info", log_message, context=EspeonContext.STRAYMONS, channel_id=log_channel_id
    )

    ends_on = active_promo["ends_on"]
    ends_on_str = f"<t:{ends_on}:F> ({datetime.utcfromtimestamp(ends_on).strftime('%Y-%m-%d %H:%M:%S UTC')})" if ends_on else "No duration set"
    log_embed = discord.Embed(
        title=f"Promo Cancelled: {active_promo['name']}",
        description=f"**Promo Name:** {active_promo['name']}\n**Prize:** {active_promo['prize']}\n**Catch Rate:** {active_promo['catch_rate']}\n**Battle Rate:** {active_promo['battle_rate']}\n**Fish Rate:** {active_promo['fish_rate']}\n**Emoji:** {active_promo['emoji']}\n**Whitelist Role ID:** {active_promo['whitelist_role_id']}\n**Number Before Claim:** {active_promo['number_before_claim']}\n**Ends On:** {ends_on_str}\n**Image URL:** {active_promo['image_url'] if active_promo['image_url'] else 'None'}\n",
        timestamp=datetime.now(),
    )
    log_embed = design_embed(
        embed=log_embed,
        user=interaction.user,
    )
    if image_url:
        log_embed.set_thumbnail(url=image_url)
    else:
        # Try to extract the URL if it's a custom emoji (static or animated)
        custom_emoji_match = re.match(r"<a?:\w+:(\d+)>", emoji)
        if custom_emoji_match:
            emoji_id = custom_emoji_match.group(1)
            is_animated = emoji.startswith("<a:")
            file_format = "gif" if is_animated else "png"
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{file_format}"
            log_embed.set_thumbnail(url=emoji_url)
        else:
            log_embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await send_webhook(
        bot=bot,
        channel=bot.get_channel(log_channel_id),
        embed=log_embed,
    )

    await loader.success(
        content=f"✅ Successfully cancelled promo '{active_promo['name']}'."
    )
