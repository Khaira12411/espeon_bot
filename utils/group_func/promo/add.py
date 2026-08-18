from datetime import datetime
import re

import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.clan_promo_db import upsert_promo
from utils.essentials.loader import pretty_defer
from utils.function.duration import parse_duration
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

STAFF_LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.bot_logs


def parse_rate(fraction: str) -> float:
    """Parses '1/50' into 0.02. Raises ValueError if numerator is not 1."""
    if fraction.strip() == "0":
        return 0.0
    try:
        numerator, denominator = fraction.strip().split("/")
        numerator, denominator = int(numerator), int(denominator)
    except Exception:
        raise ValueError(
            f"Invalid fraction format: '{fraction}'. Expected format: '1/N' or '0'"
        )
    if numerator != 1:
        raise ValueError(f"Numerator must be 1, got {numerator}.")
    if denominator == 0:
        raise ValueError("Denominator cannot be zero.")
    return numerator / denominator


def get_promo_log_settings():
    """
    Check if promo testing mode is enabled.
    """
    from utils.cache.global_variable import promo_testing_mode

    log_channel_id = None
    status = None

    if promo_testing_mode:
        log_channel_id = STRAYMONS__TEXT_CHANNELS.bot_logs
        clan_event_log_channel_id = STRAYMONS__TEXT_CHANNELS.bot_logs
        status = True
    else:
        log_channel_id = STRAYMONS__TEXT_CHANNELS.server_logs
        clan_event_log_channel_id = STRAYMONS__TEXT_CHANNELS.clan_event_log
        status = False
    return log_channel_id, status, clan_event_log_channel_id


async def add_promo_func(
    bot,
    interaction: discord.Interaction,
    name: str,
    prize: str,
    catch_rate: str,
    battle_rate: str,
    fish_rate: str,
    emoji: str,
    whitelist_role_id: int = None,
    number_before_claim: int = 0,
    image_url: str = None,
    duration: str = None,
):
    """
    Add or update a promo in the database.
    """
    log_channel_id, testing_mode, clan_event_log_channel_id = get_promo_log_settings()

    # Defer the interaction
    loader = await pretty_defer(interaction, content="Creating new promo...")

    # Parse and validate rates
    try:
        catch_rate_int = parse_rate(catch_rate)
        battle_rate_int = parse_rate(battle_rate)
        fish_rate_int = parse_rate(fish_rate)
    except ValueError as e:
        await loader.error(content=f"❌ {e}")
        return
    # Parse the duration string into a normalized string and a Unix timestamp
    duration = duration or None
    if duration is not None:
        try:
            normalized, unix_ts = parse_duration(duration)
        except ValueError as e:
            await loader.error(content=f"❌ {e}")
            return
    else:
        unix_ts = None

    # Upsert the promo into the database
    await upsert_promo(
        bot=bot,
        name=name,
        prize=prize,
        image_url=image_url,
        emoji=emoji,
        catch_rate=catch_rate,
        battle_rate=battle_rate,
        fish_rate=fish_rate,
        whitelist_role_id=whitelist_role_id,
        number_before_claim=number_before_claim,
        ends_on=unix_ts,
    )

    # Log the action
    action = "Added" if not testing_mode else "Tested adding"
    log_message = f"{action} promo '{name}' with prize '{prize}' and rates (Catch: {catch_rate}, Battle: {battle_rate}, Fish: {fish_rate})."
    unix_ts_str = f"**Ends On:** <t:{unix_ts}:F>" if unix_ts else "**Ends On:** No duration set"


    desc = f"**Promo Name:** {name}\n**Prize:** {prize}\n**Catch Rate:** {catch_rate}\n**Battle Rate:** {battle_rate}\n**Fish Rate:** {fish_rate}\n**Emoji:** {emoji}\n**Whitelist Role ID:** {whitelist_role_id}\n**Number Before Claim:** {number_before_claim}\n{unix_ts_str}\n**Image URL:** {image_url if image_url else 'None'}\n"
    log_embed = discord.Embed(
        title=f"Promo Added: {name}",
        description=desc,
        timestamp=datetime.now(),
    )


    log_embed = design_embed(
        embed=log_embed,
        user=interaction.user,
        image_url=image_url,
    )
    if image_url:
        # Try to extract the URL if it's a custom emoji (static or animated)
        log_embed.set_thumbnail(url=image_url)
    else:
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

    await loader.success(content="", embed=log_embed)
    espeon_log(
        "info", log_message, context=EspeonContext.STRAYMONS
    )
