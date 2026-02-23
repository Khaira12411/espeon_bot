# -------------------- EV Tracker View Helper --------------------
import discord
from discord.ext import commands

from utils.visuals.embeds.ev_tracker_embed import build_ev_tracker_embed
from utils.cache.cache_list import ev_tracker_cache

async def ev_tracker_view_func(bot: commands.Bot, interaction: discord.Interaction):

    channel = interaction.channel
    user_id = interaction.user.id
    guild = interaction.guild

    tracked_data = ev_tracker_cache.get(user_id)
    if not tracked_data:
        await interaction.response.send_message(
            "❌ You currently have no active EV tracker."
        )
        return

    tracked_evs = tracked_data.get("evs", {})
    tracked_goals = tracked_data.get("goals", {})

    # --- CALL THE REUSABLE EMBED FUNCTION ---
    embed, is_completed = await build_ev_tracker_embed(
        bot=bot,
        tracked_data=tracked_data,
        evs=tracked_evs,
        goals=tracked_goals,
        guild=guild,
        user_id=user_id,
        title_prefix="💜 EV Tracker",
        summary_lines=None,  # no summary for just viewing
        use_progress_bar=False,
    )

    await interaction.response.send_message(embed=embed)
