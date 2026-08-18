import re
from datetime import datetime
from random import random

import discord
import pytz
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.current_setup import CC_GUILD_ID, KHY_USER_ID, STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__ROLES
from utils.cache.cache_list import (clan_promo_cache, clan_promo_item_cache,
                                    processed_promo_listener_messages)
from utils.cache.clan_promo_item_cache import fetch_member_promo_item_cache
from utils.database.clan_promo_item_db import upsert_member_promo_item
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.function.webhook import send_webhook
from utils.group_func.promo.add import get_promo_log_settings, parse_rate
from utils.listener_func.event_checklist_caught import \
    extract_member_username_from_embed
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import espeon_log

enable_debug(f"{__name__}.promo_listener")
enable_debug(f"{__name__}.build_promo_drop_embed_and_drop_msg")

FISHING_COLOR = 8900346
PROMO_EMBED_DROP_COLOR = 0xB1A2CA


def emoji_to_name(emoji: str) -> str:
    """Extracts the name from a Discord custom emoji and returns it in title case."""
    match = re.search(r"<a?:(\w+):\d+>", emoji)
    if match:
        return match.group(1).replace("_", " ").title()
    return emoji


async def promo_listener(
    bot: discord.Client,
    before_message: discord.Message,
    after_message: discord.Message,
):

    embed = after_message.embeds[0]
    if not embed:
        debug_log(f"No embed found in message {after_message.id}. Exiting.")
        return

    embed_color = embed.color.value
    embed_description = embed.description or ""
    guild = after_message.guild

    debug_log(f"Processing message {after_message.id} | color={embed_color}")

    # Check if there is an active promo
    if not clan_promo_cache:
        espeon_log(
            "info",
            "No active promo found in cache. Skipping promo listener.",
            source="Event Checklist Caught",
        )
        return

    if after_message.id in processed_promo_listener_messages:
        debug_log(f"Message {after_message.id} already processed. Skipping.")
        return  # Already processed this message

    processed_promo_listener_messages.add(after_message.id)

    # Check if its a rare spawn based on color and description
    if "You caught" in embed_description:
        debug_log("'You caught' detected in embed description.")
        # Identify the user who caught the Pokémon
        member = await get_pokemeow_reply_member(before_message)
        if not member:
            # Extract username from embed as fallback
            username = extract_member_username_from_embed(embed)
            if username:
                from utils.cache.straymons_members_cache import \
                    fetch_straymon_member_id_by_name

                user_id = fetch_straymon_member_id_by_name(username)
                if user_id:
                    member = guild.get_member(user_id) if guild else None
                    if member:
                        espeon_log(
                            "info",
                            f"Identified member from embed author: {member.display_name}",
                            source="Event Checklist Caught",
                        )
                    else:
                        espeon_log(
                            "info",
                            f"Could not find straymon member in guild for user ID: {user_id}",
                            source="Event Checklist Caught",
                        )
                        return
                else:
                    espeon_log(
                        "info",
                        "Could not find user ID from straymons members cache.",
                        source="Event Checklist Caught",
                    )
                    return
            else:
                espeon_log(
                    "info",
                    "Could not identify member from PokéMeow reply or embed author.",
                    source="Event Checklist Caught",
                )
                return

        # TODO Member is only valid if they have the hershey role
        guild = after_message.guild

        debug_log(f"Member resolved: {member.display_name} (id={member.id})")

        if member.id != KHY_USER_ID:
            debug_log(f"Member {member.id} is not KHY_USER_ID. Skipping.")
            return
        debug_log(f"Active promo cache: {dict(clan_promo_cache)}")
        espeon_log(
            "info",
            f"Member {member.display_name} caught a Pokémon. Checking for promo drop...",
            source="Event Checklist Caught",
        )

        hershey_role = guild.get_role(STRAYMONS__ROLES.charming_hershey_espresso)
        straymon_role = guild.get_role(STRAYMONS__ROLES.straymon)
        if hershey_role not in member.roles or straymon_role not in member.roles:
            espeon_log(
                "info",
                f"Member {member.display_name} does not have the required roles. Skipping.",
                source="Event Checklist Caught",
            )
            return

        promo_drop_type = "catch"
        active_promo = clan_promo_cache.get("active_promo", {})
        rate_str = active_promo.get("catch_rate", "0")

        if embed_color == FISHING_COLOR:
            promo_drop_type = "fish"
            rate_str = str(active_promo.get("fish_rate", "0"))

        debug_log(f"Drop type: {promo_drop_type} | rate_str={rate_str!r}")

        rate = parse_rate(rate_str)
        debug_log(f"Parsed rate: {rate} ({rate_str})")
        if rate == 0 or random() >= rate:
            debug_log(f"No promo drop for {member.display_name}. rate={rate}")
            espeon_log(
                "info",
                f"Member {member.display_name} did not get a promo drop. Rate: {rate_str}",
                source="Event Checklist Caught",
            )
            return  # Not a successful promo drop

        # Get settings for logging
        log_channel_id, testing_mode, clan_event_log_channel_id = (
            get_promo_log_settings()
        )

        debug_log(f"Promo drop triggered for {member.display_name} via {promo_drop_type}.")
        # Get promo embed details
        promo_embed, drop_msg = await build_promo_drop_embed_and_drop_msg(
            bot=bot,
            member=member,
            drop_type=promo_drop_type,
            msg_link=after_message.jump_url,
        )

        await after_message.channel.send(content=drop_msg)
        await send_webhook(
            bot=bot,
            channel=bot.get_channel(clan_event_log_channel_id),
            embed=promo_embed,
        )


async def build_promo_drop_embed_and_drop_msg(
    bot: discord.Client,
    member: discord.Member,
    drop_type: str,
    msg_link: str,
):
    """Builds the embed for the promo drop notification."""

    footer_emoji = "💜"
    active_promo = clan_promo_cache.get("active_promo", {})
    promo_name = active_promo.get("name", "Unknown Promo")
    promo_emoji = active_promo.get("emoji", "")

    debug_log(f"Building drop embed | promo={promo_name!r} member={member.display_name} drop_type={drop_type}")

    # Fetch the member's promo item details from the cache
    member_promo_item = fetch_member_promo_item_cache(promo_name, member.id)

    if not member_promo_item:
        debug_log(f"No promo item cache found for {member.display_name}. Upserting with drops=0.")
        # Upsert the member's promo item in database first
        await upsert_member_promo_item(bot, promo_name, member.id, member.name, drops=0)
        member_promo_item = fetch_member_promo_item_cache(promo_name, member.id)

    member_promo_item_drops = (
        member_promo_item.get("drops", 0) if member_promo_item else 0
    )

    new_drops = member_promo_item_drops + 1
    debug_log(f"Updating drops for {member.display_name}: {member_promo_item_drops} -> {new_drops}")
    # Update the member's promo item drops in the database
    await upsert_member_promo_item(
        bot, promo_name, member.id, member.name, drops=new_drops
    )

    if drop_type == "catch":
        drop_type_text = "Catching"
        drop_type_emoji = Espeon_Emoji.purple_ball
    elif drop_type == "fish":
        drop_type_text = "Fishing"
        drop_type_emoji = Espeon_Emoji.purple_fishing

    drop_type_str = f"{drop_type_emoji} {drop_type_text}"
    promo_emoji_name = emoji_to_name(promo_emoji)

    title = f"{promo_emoji} {promo_emoji_name} Drop!"
    desc = (
        f"Promo: {promo_name}\n"
        f"Member: {member.mention}\n"
        f"Drop Type: {drop_type_str}\n"
        f"Total Drops: {new_drops}\n"
    )
    embed = discord.Embed(
        title=title,
        url=msg_link,
        description=desc,
        color=PROMO_EMBED_DROP_COLOR,
        timestamp=datetime.now(),
    )
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

    custom_emoji_match = re.match(r"<a?:\w+:(\d+)>", promo_emoji)
    if custom_emoji_match:
        emoji_id = custom_emoji_match.group(1)
        is_animated = promo_emoji.startswith("<a:")
        file_format = "gif" if is_animated else "png"
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{file_format}"
        embed.set_thumbnail(url=emoji_url)
    else:
        embed.set_thumbnail(url=member.display_avatar.url)

    drop_msg = f"{member.mention} has found a {promo_emoji} **{promo_emoji_name}** while {drop_type_text.lower()}! You now have a total of {promo_emoji} **{new_drops}**!"
    return embed, drop_msg
