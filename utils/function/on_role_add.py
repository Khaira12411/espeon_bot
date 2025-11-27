from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.current_setup import STRAYMONS_GUILD_ID
from config.paldea_galar_dict import rarity_meta
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import (
    server_shop_cache,
    straymon_member_cache,
    user_balance_cache,
)
from utils.database.server_currency import get_user_balance
from utils.database.server_shop import fetch_item_by_name, remove_item_by_name
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.loggers.espeon_log import EspeonContext, espeon_log

WEEKLY_ROLES = [
    STRAYMONS__ROLES.weekly_angler,
    STRAYMONS__ROLES.weekly_grinder,
    STRAYMONS__ROLES.weekly_guardian,
]


# 🍭──────────────────────────────
#   🎀 Event: On Role Add
# 🍭──────────────────────────────
async def handle_role_add(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    """Handle role addition events."""
    role_id = role.id

    # ————————————————————————————————
    # 🩵 Straymon Weekly Role Add
    # ————————————————————————————————
    if role_id in WEEKLY_ROLES:
        # Check if user has all weekly roles
        espeon_log(
            tag="info",
            message=f"Checking weekly roles for {member} after receiving role {role.name}.",
        )
        has_all_weekly_roles = all(
            member.get_role(weekly_role_id) is not None
            for weekly_role_id in WEEKLY_ROLES
        )
        if has_all_weekly_roles:
            # Check if gardelette box is still in shop
            espeon_log(
                tag="info",
                message=f"{member} has obtained all weekly roles. Checking for Gardelette Box in shop.",
            )
            gardelette_box_item = None
            try:
                gardelette_box_item = await fetch_item_by_name(bot, "Gardelette Box")
            except Exception as e:
                espeon_log(
                    tag="error",
                    message=(
                        f"Error fetching 'Gardelette Box' from shop for {member}: {e}"
                    ),
                )
                gardelette_box_item = None
            if not gardelette_box_item:
                espeon_log(
                    tag="info",
                    message=f"Gardelette Box not found in shop for {member}.",
                )
                return
            if gardelette_box_item:
                user_balance_info = user_balance_cache.get(member.id)
                if user_balance_info:
                    # Check if user has bought gardelette box
                    has_gardelette_box = user_balance_info.get(
                        "bought_gardelette_box", "no"
                    )
                    if has_gardelette_box == "yes":
                        # Remove gardelette box from shop
                        await remove_item_by_name(bot, "Gardelette Box")
                        espeon_log(
                            tag="info",
                            message=f"Removed 'Gardelette Box' from shop as {member} has obtained all weekly roles.",
                        )
                        embed = discord.Embed(
                            title="🌸 Gardelette Quest Completed 🌸",
                            description=(
                                f"Congratulations {member.mention}!\n\n"
                                "You have obtained all Weekly Roles and completed the Gardelette Box Quest!\n"
                                f"{Espeon_Emoji.pink_flower} Please forward this message in <#1359856208961601638> and wait for Skaia to hand your prize."
                            ),
                            color=COLOR,
                            timestamp=datetime.now(),
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_author(
                            name=member.display_name, icon_url=member.display_avatar.url
                        )
                        user_info = straymon_member_cache.get(member.id)
                        user_channel_id = user_info.get("channel_id")
                        if user_channel_id:
                            user_channel = member.guild.get_channel(user_channel_id)
                            if user_channel:
                                await user_channel.send(embed=embed)

                        # Log gardelette quest completion
                        log_embed = discord.Embed(
                            title="🌸 Gardelette Quest Completed 🌸",
                            description=(
                                f"- **User:** {member.mention}\n"
                            ),
                            color=COLOR,
                            timestamp=datetime.now(),
                        )
                        log_embed.set_author(
                            name=member.display_name, icon_url=member.display_avatar.url
                        )
                        log_embed.set_thumbnail(url=member.display_avatar.url)
                        log_embed.set_footer(
                            text=f"User ID: {member.id}",
                            icon_url=(
                                member.guild.icon.url
                                if member.guild and member.guild.icon
                                else None
                            ),
                        )

                        cafe_log_channel = member.guild.get_channel(STRAYMONS__TEXT_CHANNELS.cafe_logs)
                        clan_event_log_channel = member.guild.get_channel(STRAYMONS__TEXT_CHANNELS.clan_event_log)
                        if cafe_log_channel:
                            await cafe_log_channel.send(embed=log_embed)
                        if clan_event_log_channel:
                            await clan_event_log_channel.send(embed=log_embed)
                    else:
                        espeon_log(
                            tag="info",
                            message=f"{member} has not purchased Gardelette Box despite having all weekly roles.",
                        )
            else:
                espeon_log(
                    tag="info",
                    message=f"Gardelette Box not found in shop when {member} obtained all weekly roles.",
                )
