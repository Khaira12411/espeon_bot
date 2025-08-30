# 🟣────────────────────────────────────────────
#           💜 EV Tracker Brain: Reset 💜
# 🟣────────────────────────────────────────────
from datetime import datetime

import discord

from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.group_func.ev_tracker.ev_tracker_db_func import (
    delete_tracked_ev,
    get_tracked_ev,
)
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

STAFF_LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.server_logs


async def ev_tracker_reset_func(bot, interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id
    from utils.cache.ev_tracker_cache import ev_tracker_cache, load_ev_tracker_cache

    try:
        # -------------------- Step 0: Fetch tracked Pokémon --------------------
        tracked_data = await get_tracked_ev(bot, user_id)
        tracked_list = tracked_data["pokemon"] if tracked_data else None

        # -------------------- Step 1: Remove from DB --------------------
        deleted = await delete_tracked_ev(bot, user_id)
        if not deleted:
            await interaction.response.send_message(
                f"❌ You aren't EV tracking any mons!", ephemeral=True
            )
            return

        # -------------------- Step 2: Build confirmation embed --------------------
        description = (
            f"✅ Your current EV tracker for **{tracked_list}** has been reset!\n"
            f"Use `/ev-tracker add` to track a new Pokémon!"
            if tracked_list
            else "✅ Your EV tracker has been reset! Use `/ev-tracker add` to track a new Pokémon!"
        )
        embed = discord.Embed(
            title="EV Tracker Reset",
            description=description,
            color=0xFF99FF,
            timestamp=datetime.utcnow(),
        )
        embed = design_embed(embed, interaction.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # -------------------- Step 3: Log to staff --------------------
        staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
        if staff_channel:
            staff_embed = discord.Embed(
                title="EV Tracker Reset",
                description=f"User **{user}** reset all their EVs",
                color=0xAA66FF,
                timestamp=datetime.utcnow(),
            )
            await staff_channel.send(embed=staff_embed)

        # 💜 Load EV Tracker cache
        await load_ev_tracker_cache(bot)
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to reset EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await interaction.response.send_message(
            f"❌ Failed to reset your EVs: {e}", ephemeral=True
        )
