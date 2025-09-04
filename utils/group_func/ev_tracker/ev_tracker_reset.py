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
from utils.visuals.gif import fetch_pokemon_gif


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › EV Tracker Reset ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def ev_tracker_reset_func(bot, interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id
    from utils.cache.ev_tracker_cache import ev_tracker_cache, load_ev_tracker_cache

    try:
        # ✨──────── Step 0 › Defer & Fetch Tracked Pokémon ─────✨
        handle = await pretty_defer(
            interaction=interaction, content="Resetting your EV Tracker..."
        )
        tracked_data = await get_tracked_ev(
            bot, user_id
        )  # fetch tracked Pokémon from DB
        tracked_list = tracked_data["pokemon"] if tracked_data else None

        # ✨──────── Step 1 › Remove from DB ─────✨
        deleted = await delete_tracked_ev(bot, user_id)  # delete tracked data
        if not deleted:
            await handle.stop(
                content="❌ You aren't EV tracking any mons!"
            )  # early return if none
            return

        # ✨──────── Step 2 › Build Confirmation Embed ─────✨
        thumbnail_url = interaction.user.display_avatar.url  # fallback avatar
        description = (
            f"✅ Your current EV tracker for **{tracked_list}** has been reset!"
            if tracked_list
            else "✅ Your EV tracker has been reset! Use `/ev-tracker add` to track a new Pokémon!"
        )
        embed = discord.Embed(
            title="EV Tracker Reset",
            description=description,
            color=0xFF99FF,
        )
        footer_text = f"Use `/ev-tracker add` to track a new Pokémon!"
        # 💜 Fetching Pokémon GIF to make it extra cute 💜
        if tracked_list:
            pokemon_gif_url = await fetch_pokemon_gif(pokemon=tracked_list)
            if pokemon_gif_url:
                thumbnail_url = pokemon_gif_url  # replace avatar with Pokémon GIF

        embed = design_embed(
            embed=embed,
            user=interaction.user,
            thumbnail_url=thumbnail_url,
            footer_text=footer_text,
        )  # apply Espeon embed styling

        await handle.stop(embed=embed)  # send the confirmation embed

        # ✨──────── Step 3 › Log Reset to Staff ─────✨
        staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
        desc = format_bulletin_desc(
            "Member", user.mention, "Pokemon", tracked_list
        )  # mini info
        if staff_channel:
            staff_embed = discord.Embed(
                title="EV Tracker Reset",
                description=desc,
            )
            staff_embed = design_embed(
                embed=staff_embed, user=user, thumbnail_url=thumbnail_url
            )  # staff embed with same cute thumbnail
            await staff_channel.send(embed=staff_embed)  # log to staff

        # 💜 Refresh EV Tracker Cache 💜
        await load_ev_tracker_cache(bot)

    except Exception as e:
        # ❌ Error logging if something goes wrong
        espeon_log(
            tag="error",
            message=f"Failed to reset EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await interaction.response.send_message(
            f"❌ Failed to reset your EVs: {e}", ephemeral=True
        )
