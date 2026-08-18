import re
from datetime import datetime

import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.clan_promo_db import fetch_active_promo, upsert_promo
from utils.essentials.loader import pretty_defer
from utils.function.duration import parse_duration
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

from .add import get_promo_log_settings, parse_rate

STAFF_LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.bot_logs



async def edit_promo_func(
    bot,
    interaction: discord.Interaction,
    prize: str = None,
    catch_rate: int = None,
    battle_rate: int = None,
    fish_rate: int = None,
    emoji: str = None,
    whitelist_role_id: int = None,
    number_before_claim: int = None,
    image_url: str = None,
    duration: str = None,
):
    """
    Edit the active promo in the database.
    """


    log_channel_id, testing_mode, clan_event_log_channel_id = get_promo_log_settings()

    # Defer the interaction
    loader = await pretty_defer(interaction, content="Editing active promo...")

    # Check if there is an active promo
    active_promo = await fetch_active_promo(bot)
    if not active_promo:
        await loader.error(
            content="❌ There is no active promo to edit. Please add a promo first."
        )
        return

    if all(p is None for p in (prize, catch_rate, battle_rate, fish_rate, emoji, whitelist_role_id, number_before_claim, image_url, duration)):
        await loader.error(content="❌ Please provide at least one parameter to edit.")
        return

    # Get old values for logging
    old_name = active_promo["name"]
    old_prize = active_promo["prize"]
    old_catch_rate = active_promo["catch_rate"]
    old_battle_rate = active_promo["battle_rate"]
    old_fish_rate = active_promo["fish_rate"]
    old_emoji = active_promo["emoji"]
    old_whitelist_role_id = active_promo["whitelist_role_id"]
    old_number_before_claim = active_promo["number_before_claim"]
    old_ends_on = active_promo["ends_on"]
    old_image_url = active_promo["image_url"]

    # Parse and validate rates, falling back to existing values when None
    prize = prize if prize is not None else old_prize
    emoji = emoji if emoji is not None else old_emoji
    number_before_claim = number_before_claim if number_before_claim is not None else old_number_before_claim
    catch_rate = catch_rate if catch_rate is not None else old_catch_rate
    battle_rate = battle_rate if battle_rate is not None else old_battle_rate
    fish_rate = fish_rate if fish_rate is not None else old_fish_rate
    try:
        catch_rate_int = parse_rate(catch_rate)
        battle_rate_int = parse_rate(battle_rate)
        fish_rate_int = parse_rate(fish_rate)
    except ValueError as e:
        await loader.error(content=f"❌ {e}")
        return
    # Parse the duration string into a normalized string and a Unix timestamp
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
        name=old_name,
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
    action = "Edited" if not testing_mode else "Tested editing"
    log_message = f"{action} promo '{old_name}' with prize '{prize}' and rates (Catch: {catch_rate}, Battle: {battle_rate}, Fish: {fish_rate})."


    parts = []
    parts.append(f"**Promo Name:** {old_name}")
    parts.append(f"**Prize:** {old_prize} → {prize}" if old_prize != prize else f"**Prize:** {prize}")
    if catch_rate_int != 0:
        parts.append(f"**Catch Rate:** {old_catch_rate} → {catch_rate}" if old_catch_rate != catch_rate else f"**Catch Rate:** {catch_rate}")
    if battle_rate_int != 0:
        parts.append(f"**Battle Rate:** {old_battle_rate} → {battle_rate}" if old_battle_rate != battle_rate else f"**Battle Rate:** {battle_rate}")
    if fish_rate_int != 0:
        parts.append(f"**Fish Rate:** {old_fish_rate} → {fish_rate}" if old_fish_rate != fish_rate else f"**Fish Rate:** {fish_rate}")
    parts.append(f"**Emoji:** {old_emoji} → {emoji}" if old_emoji != emoji else f"**Emoji:** {emoji}")
    if whitelist_role_id is not None:
        parts.append(f"**Whitelist Role ID:** <@&{old_whitelist_role_id}> → <@&{whitelist_role_id}>" if old_whitelist_role_id != whitelist_role_id else f"**Whitelist Role ID:** <@&{whitelist_role_id}>")
    if number_before_claim != 0:
        parts.append(f"**Number Before Claim:** {old_number_before_claim} → {number_before_claim}" if old_number_before_claim != number_before_claim else f"**Number Before Claim:** {number_before_claim}")
    if unix_ts is None:
        parts.append("**Ends On:** No duration set")
    else:
        parts.append(f"**Ends On:** <t:{old_ends_on}:F> → <t:{unix_ts}:F> ({normalized})" if old_ends_on != unix_ts else f"**Ends On:** <t:{unix_ts}:F> ({normalized})")
    if image_url is not None:
        parts.append(f"**Image URL:** {old_image_url} → {image_url}" if old_image_url != image_url else f"**Image URL:** {image_url}")

    desc = "\n".join(parts) + "\n"
    log_embed = discord.Embed(
        title=f"Promo Edited: {old_name}",
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
