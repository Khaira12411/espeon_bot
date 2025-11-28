import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.paldea_galar_dict import rarity_meta
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import server_shop_cache, user_balance_cache
from utils.database.server_currency import get_user_balance
from utils.database.server_shop import fetch_item_by_name, remove_item_by_name
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

from .event_checklist_caught import is_dec_28_1pm_or_later_manila

TEST_BOT_LOG_ID = 1220786187401302036
REAL_BOT_LOG_ID = 1076441765059502233
BOT_LOG_ID = TEST_BOT_LOG_ID
# TODO insert mon later
CHECKLIST_REWARD_MON = "shiny yamper"

enable_debug(f"{__name__}.handle_code_claim")


async def handle_code_claim(bot: discord.Client, message: discord.Message):
    """
    Handles code claim messages and rewards users accordingly.
    """
    content = message.content
    if not content:
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    guild = message.guild

    if is_dec_28_1pm_or_later_manila():
        # dont process if after dec 28 1pm manila time
        espeon_log(
            "info",
            "Current time is after Dec 28, 1 PM Manila time. Skipping code claim processing.",
            source="Code Claim Listener",
        )
        return

    # Extract pokemon name
    pokemon_name = re.search(r"\*\*(.*?)\*\*", content)
    if not pokemon_name:
        espeon_log(
            tag="warn",
            message="Could not extract pokemon name from code claim message.",
            label="💖 CODE CLAIM LISTENER",
        )
        return
    cleaned_pokemon_name = pokemon_name.group(1).lower().strip()
    espeon_log(
        tag="info",
        message=f"Extracted pokemon name: {cleaned_pokemon_name}",
        label="💖 CODE CLAIM LISTENER",
    )
    original_name = None
    if cleaned_pokemon_name.lower() == CHECKLIST_REWARD_MON:
        original_name = cleaned_pokemon_name
        if "shiny" in cleaned_pokemon_name:
            cleaned_pokemon_name = cleaned_pokemon_name.replace("shiny ", "")
            rarity = "shiny"
            debug_log(
                f"Detected shiny rarity for pokemon: {cleaned_pokemon_name}",
            )
        elif "golden" in cleaned_pokemon_name:
            cleaned_pokemon_name = cleaned_pokemon_name.replace("golden ", "")
            rarity = "golden"
            debug_log(
                f"Detected golden rarity for pokemon: {cleaned_pokemon_name}",
            )

        rarity_info = rarity_meta.get(rarity, {})
        rarity_emoji = rarity_info.get("emoji", "")
        rarity_color = rarity_info.get("color", COLOR)

        display_name = f"{rarity_emoji} {cleaned_pokemon_name.title()}"
        # Check if there is still Melaryne Box in shop
        melaryne_box_item = None
        melaryne_box_item = await fetch_item_by_name(bot, "Melaryne Box")
        if not melaryne_box_item:
            espeon_log(
                tag="warn",
                message="Melaryne Box item not found in shop database.",
                label="💖 CODE CLAIM LISTENER",
            )
            return

        user_balance_info = user_balance_cache.get(member.id)
        if not user_balance_info:
            espeon_log(
                tag="info",
                message=f"User balance info not found in cache for user_id: {member.id}.",
                label="💖 CODE CLAIM LISTENER",
            )
            return
        has_melaryne_box = user_balance_info.get("bought_melaryne_box", "no")
        if has_melaryne_box == "no":
            espeon_log(
                tag="info",
                message=(
                    f"User {member} has not purchased Melaryne Box despite "
                    f"claiming a code for '{original_name}'."
                ),
                label="💖 CODE CLAIM LISTENER",
            )
            return
        elif has_melaryne_box == "yes":
            # Remove Melaryne Box from shop
            await remove_item_by_name(bot, "Melaryne Box")
            espeon_log(
                tag="info",
                message=(
                    f"Melaryne Box has been removed from the shop after "
                    f"{member} claimed a code for '{original_name}'."
                ),
                label="💖 CODE CLAIM LISTENER",
            )
            quest_complete_embed = discord.Embed(
                title="🌸 Melaryne Quest Complete! 🌸",
                description=(
                    f"Congratulations {member.mention}! You have completed the Melaryne Quest by "
                    f"claiming a code for **{display_name}**.\n\n"
                    f"{Espeon_Emoji.pink_flower} Please forward this message in <#1359856208961601638> and wait for Skaia to hand your prize."
                ),
                color=COLOR,
                timestamp=datetime.now(),
            )
            quest_complete_embed = design_embed(
                embed=quest_complete_embed, user=member, pokemon_name=original_name
            )
            await message.channel.send(embed=quest_complete_embed)

            # Log quest completion in clan event logs channel
            quest_complete_log_embed = discord.Embed(
                title="🌸 Melaryne Quest Completed 🌸",
                description=(
                    f"[Jump to Message]({message.jump_url})\n"
                    f"{member} has completed the Melaryne Quest by claiming a code for "
                    f"**{display_name}**. The Melaryne Box has been removed from the shop."
                ),
                color=rarity_color,
                timestamp=datetime.now(),
            )
            quest_complete_log_embed = design_embed(
                embed=quest_complete_log_embed, user=member, pokemon_name=original_name
            )
            clan_event_log_channel = guild.get_channel(
                STRAYMONS__TEXT_CHANNELS.clan_event_logs
            )
            if clan_event_log_channel:
                await clan_event_log_channel.send(embed=quest_complete_log_embed)
            cafe_log_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.cafe_logs)
            if cafe_log_channel:
                await cafe_log_channel.send(embed=quest_complete_log_embed)
