import re
from datetime import datetime

import discord

from config.aesthetic import *
from config.straymons_constants import (STRAYMONS__ROLES,
                                        STRAYMONS__TEXT_CHANNELS)
from utils.cache.clan_promo_item_cache import fetch_member_promo_item_cache
from utils.database.clan_promo_db import fetch_active_promo, upsert_promo
from utils.database.clan_promo_item_db import upsert_member_promo_item
from utils.essentials.loader import pretty_defer
from utils.function.duration import parse_duration
from utils.function.webhook import send_webhook
from utils.listener_func.promo_caught import PROMO_EMBED_DROP_COLOR
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

from .add import get_promo_log_settings, parse_rate


async def view_promo_func(bot, interaction: discord.Interaction):
    """Views the active promo"""

    # Defer the interaction
    loader = await pretty_defer(interaction, content="Viewing active promo...", ephemeral=False)

    # Check if there is an active promo
    active_promo = await fetch_active_promo(bot)
    if not active_promo:
        await loader.error(
            content="❌ There is no active promo to view."
        )
        return
    member = interaction.user
    promo_name = active_promo["name"]
    promo_prize = active_promo["prize"]
    promo_catch_rate = active_promo["catch_rate"]
    promo_battle_rate = active_promo["battle_rate"]
    promo_fish_rate = active_promo["fish_rate"]
    promo_emoji = active_promo["emoji"]
    promo_whitelist_role_id = active_promo["whitelist_role_id"]
    promo_number_before_claim = active_promo["number_before_claim"]
    promo_ends_on = active_promo["ends_on"]
    promo_image_url = active_promo["image_url"]

    # Prepare string lines
    promo_name_str = f"**Name:** {promo_name}\n"
    promo_prize_str = f"**Prize:** {promo_prize}\n"
    promo_catch_rate_str = f"**Catch Rate:** {promo_catch_rate}\n" if promo_catch_rate and parse_rate(promo_catch_rate) != 0 else ""
    promo_fish_rate_str = f"**Fish Rate:** {promo_fish_rate}\n" if promo_fish_rate and parse_rate(promo_fish_rate) != 0 else ""
    promo_battle_rate_str = f"**Battle Rate:** {promo_battle_rate}\n" if promo_battle_rate and parse_rate(promo_battle_rate) != 0 else ""
    promo_emoji_str = f"**Emoji:** {promo_emoji}\n" if promo_emoji else ""
    promo_whitelist_role_str = (
        f"**Whitelist Role:** <@&{promo_whitelist_role_id}>\n"  if promo_whitelist_role_id else ""
    )
    promo_number_before_claim_str = (
        f"**Drops Before Claim:** {promo_number_before_claim}\n" if promo_number_before_claim else ""
    )
    promo_ends_on_str = (
        f"**Ends On:** <t:{promo_ends_on}:F> (<t:{promo_ends_on}:R>)\n" if promo_ends_on else ""
    )

    promo_info_desc = (
        promo_name_str
        + promo_prize_str
        + promo_catch_rate_str
        + promo_fish_rate_str
        + promo_battle_rate_str
        + promo_emoji_str
        + promo_whitelist_role_str
        + promo_number_before_claim_str
        + promo_ends_on_str

    )

    # Prepare user's promo items desc

    # Fetch the member's promo item details from the cache
    member_promo_item = fetch_member_promo_item_cache(promo_name, member.id)

    if not member_promo_item:
        # Upsert the member's promo item in database first
        await upsert_member_promo_item(bot, promo_name, member.id, member.name, drops=0)
        member_promo_item = fetch_member_promo_item_cache(promo_name, member.id)

    member_promo_item_drops = (
        member_promo_item.get("drops", 0) if member_promo_item else 0
    )
    member_promo_item_drops_str = f"\n**Your Total Drops:** {promo_emoji} {member_promo_item_drops}\n"

    embed_desc = promo_info_desc + member_promo_item_drops_str

    embed = discord.Embed(
        title=f"Active Promo: {promo_name}",
        description=embed_desc,
        color=PROMO_EMBED_DROP_COLOR,
        timestamp=datetime.now(),
    )

    custom_emoji_match = re.match(r"<a?:\w+:(\d+)>", promo_emoji)
    if custom_emoji_match:
        emoji_id = custom_emoji_match.group(1)
        is_animated = promo_emoji.startswith("<a:")
        file_format = "gif" if is_animated else "png"
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{file_format}"
        embed.set_thumbnail(url=emoji_url)

    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

    await loader.success(content="", embed=embed)