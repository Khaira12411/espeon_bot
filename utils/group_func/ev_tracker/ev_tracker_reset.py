# 🟣────────────────────────────────────────────
#           💜 EV Tracker Brain: Reset 💜
# 🟣────────────────────────────────────────────
from datetime import datetime

import discord

from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.essentials.loader import pretty_defer
from utils.group_func.ev_tracker.ev_tracker_db_func import (
    delete_tracked_ev,
    get_tracked_ev,
)
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc

STAFF_LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.server_logs
from config.aesthetic import *
from utils.visuals.embeds.get_pokemon_gif import get_pokemon_gif
from utils.visuals.gif import fetch_pokemon_gif
from utils.function.webhook import send_webhook

# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › EV Tracker Reset ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def ev_tracker_reset_func(bot, interaction: discord.Interaction):
    from utils.cache.ev_tracker_cache import get_ev_tracker, remove_ev_tracker_cache

    user = interaction.user
    user_id = user.id

    try:
        # ✨──────── Step 0 › Defer & Fetch Tracked Pokemon ─────✨
        handle = await pretty_defer(
            interaction=interaction, content="Resetting your EV Tracker..."
        )

        # Prefer cache first
        cached = get_ev_tracker(user_id)
        tracked_list = cached["pokemon"] if cached else None

        # Fallback to DB if needed
        if not tracked_list:
            tracked_data = await get_tracked_ev(bot, user_id)
            tracked_list = tracked_data["pokemon"] if tracked_data else None

        # ✨──────── Step 1 › Remove from DB ─────✨
        deleted = await delete_tracked_ev(bot, user_id)
        if not deleted:
            await handle.error(content="You aren't EV tracking any mons!")
            return

        # 💜 Remove from cache immediately
        remove_ev_tracker_cache(user_id)

        # ✨──────── Step 2 › Build Confirmation Embed ─────✨
        thumbnail_url = interaction.user.display_avatar.url
        description = (
            f"✅ Your current EV tracker for **{tracked_list}** has been reset!"
            if tracked_list
            else "✅ Your EV tracker has been reset! Use `/ev-tracker add` to track a new Pokemon!"
        )

        if tracked_list:
            pokemon_gif_url = get_pokemon_gif(tracked_list)
            if pokemon_gif_url:
                thumbnail_url = pokemon_gif_url

        embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_broom} EV Tracker Reset",
            description=description,
            color=0xFF99FF,
        )
        embed = design_embed(
            embed=embed,
            user=user,
            thumbnail_url=thumbnail_url,
            footer_text="Use `/ev-tracker add` to track a new Pokemon!",
        )
        await handle.success(content="", embed=embed)

        # ✨──────── Step 3 › Staff log ─────✨
        staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
        if staff_channel:
            desc = format_bulletin_desc("Member", user.mention, "Pokemon", tracked_list)
            staff_embed = discord.Embed(
                title=f"{Espeon_Emoji.purple_broom} EV Tracker Reset",
                description=desc,
            )
            staff_embed = design_embed(
                embed=staff_embed, user=user, thumbnail_url=thumbnail_url
            )
            await send_webhook(
                bot=bot,
                channel=staff_channel,
                embed=staff_embed,
            )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to reset EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await handle.error(content=f"Failed to reset your EVs: {e}")
