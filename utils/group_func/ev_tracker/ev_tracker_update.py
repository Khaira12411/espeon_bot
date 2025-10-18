# 🟣────────────────────────────────────────────
#           💜 EV Tracker Brain: Update 💜
# 🟣────────────────────────────────────────────
from datetime import datetime

import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.essentials.loader import pretty_defer
from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc
from utils.visuals.gif import fetch_pokemon_gif
from utils.cache.cache_list import ev_tracker_cache
MAX_EVS_PER_STAT = 252
MAX_TOTAL_EVS = 510
STAFF_LOG_CHANNEL_ID = (
    STRAYMONS__TEXT_CHANNELS.server_logs
)  # replace with your staff log channel ID


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › EV Update ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def ev_tracker_update_func(
    bot,
    interaction: discord.Interaction,
    hp=None,
    atk=None,
    spa=None,
    def_=None,
    spd=None,
    spe=None,
):
    from utils.cache.ev_tracker_cache import load_ev_tracker_cache

    # ⏳ Pretty loader while fetching
    handle = await pretty_defer(
        interaction=interaction, content="Fetching your EV tracker info..."
    )
    user = interaction.user
    user_id = user.id

    # -------------------- Step 1: Determine Pokemon --------------------
    tracked = ev_tracker_cache.get(user_id)
    if not tracked:
        await handle.stop(
            content="❌ You have no Pokemon currently being tracked. Use `/ev-tracker add` first.",
        )
        return

    pokemon_data = tracked
    pokemon_title = pokemon_data["pokemon"]
    dex_number = pokemon_data["dex_number"]

    # -------------------- Step 2: Collect EV stats/ Verify Input --------------------
    await handle.edit(content="Verifying your Input....")
    evs_to_track = {}
    goals_to_track = {}
    total_goal_sum = 0

    for stat, val in (
        ("hp", hp),
        ("atk", atk),
        ("spa", spa),
        ("def", def_),
        ("spd", spd),
        ("spe", spe),
    ):
        if val is not None:
            val_str = str(val).strip()

            # ✅ Clear stat if user inputs 0
            if val_str == "0":
                evs_to_track[stat] = None
                goals_to_track.pop(stat, None)
                continue

            if "/" not in val_str:
                await handle.stop(
                    content=f"❌ Invalid format for **{stat.upper()}**. Use `current/goal` (e.g., 0/252)."
                )
                return
            parts = val_str.split("/")
            try:
                current = int(parts[0].strip())
                goal = int(parts[1].strip()) if len(parts) > 1 else None
            except ValueError:
                content = (
                    f"❌ Invalid number for **{stat.upper()}**. Use integers only."
                )
                await handle.stop(content=content)
                return
            if goal is not None and goal > MAX_EVS_PER_STAT:
                content = (
                    f"❌ Goal for **{stat.upper()}** cannot exceed {MAX_EVS_PER_STAT}.",
                )
                await handle.stop(content=content)
                return
            evs_to_track[stat] = current
            if goal is not None:
                goals_to_track[stat] = goal
                total_goal_sum += goal

    if not evs_to_track:
        await handle.stop(content="❌ You must provide at least one EV to update.")
        return

    if total_goal_sum > MAX_TOTAL_EVS:
        await handle.stop(
            content=f"❌ Total EV goal ({total_goal_sum}) exceeds {MAX_TOTAL_EVS}.",
        )
        return

    # -------------------- Step 3: Save to database --------------------
    await handle.edit(content="Updating your settings....")
    try:
        await add_or_update_ev(
            bot,
            user_id,
            user.name,
            pokemon_title,
            evs_to_track,
            goals=goals_to_track,
            dex_number=dex_number,
        )

        # 💜 Update cache directly for this user instead of full reload
        from utils.cache.ev_tracker_cache import (
            get_ev_tracker,
            insert_ev_tracker_cache,
            update_ev_tracker_cache,
        )

        cached_user = get_ev_tracker(user_id)
        if cached_user:
            # Update only the stats that were provided
            for stat, current in evs_to_track.items():
                update_ev_tracker_cache(user_id, stat, current, is_goal=False)
            for stat, goal in goals_to_track.items():
                update_ev_tracker_cache(user_id, stat, goal, is_goal=True)
        else:
            # User not in cache? Insert full row
            insert_ev_tracker_cache(
                {
                    "user_id": user_id,
                    "user_name": user.name,
                    "pokemon": pokemon_title,
                    "dex_number": dex_number,
                    **evs_to_track,
                    **{f"{k}_goal": v for k, v in goals_to_track.items()},
                }
            )

        # Build embed for user confirmation
        description_lines = [
            f"**Pokemon:** {pokemon_title} #{dex_number}\n {Espeon_Emoji.purple_pie} **EVs:**"
        ]
        for stat, current in evs_to_track.items():
            goal = goals_to_track.get(stat)
            display_current = current if current is not None else "-"
            display_goal = goal if goal is not None else "-"
            description_lines.append(
                f"- {stat.upper()}: {display_current}/{display_goal}"
            )
        description_text = "\n".join(description_lines)

        embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_three_flowers} EV Tracker Updated",
            description=description_text,
            color=0xFF99FF,
        )
        embed = design_embed(embed=embed, user=user, pokemon_name=pokemon_title)

        # Sends final embed
        await handle.stop(embed=embed)

        espeon_log(
            tag="sent",
            message=f"User {user_id} updated {pokemon_title} EVs: {evs_to_track} with goals {goals_to_track}",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to update EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await interaction.response.send_message(
            f"❌ Failed to update EVs: {e}", ephemeral=True
        )
