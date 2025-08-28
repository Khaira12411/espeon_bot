# 🟣────────────────────────────────────────────
#           💜 EV Tracker Brain: Update 💜
# 🟣────────────────────────────────────────────
from datetime import datetime

import discord
from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.visuals.embeds.visual_helpers import set_embed_user_context
from utils.loggers.espeon_log import EspeonContext, espeon_log
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS

MAX_EVS_PER_STAT = 252
MAX_TOTAL_EVS = 510
STAFF_LOG_CHANNEL_ID = (
    STRAYMONS__TEXT_CHANNELS.server_logs
)  # replace with your staff log channel ID


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
    from utils.cache.ev_tracker_cache import ev_tracker_cache, load_ev_tracker_cache

    user = interaction.user
    user_id = user.id

    # -------------------- Step 1: Collect EV stats --------------------
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
                await interaction.response.send_message(
                    f"❌ Invalid format for **{stat.upper()}**. Use `current/goal` (e.g., 0/252).",
                    ephemeral=True,
                )
                return
            parts = val_str.split("/")
            try:
                current = int(parts[0].strip())
                goal = int(parts[1].strip()) if len(parts) > 1 else None
            except ValueError:
                await interaction.response.send_message(
                    f"❌ Invalid number for **{stat.upper()}**. Use integers only.",
                    ephemeral=True,
                )
                return
            if goal is not None and goal > MAX_EVS_PER_STAT:
                await interaction.response.send_message(
                    f"❌ Goal for **{stat.upper()}** cannot exceed {MAX_EVS_PER_STAT}.",
                    ephemeral=True,
                )
                return
            evs_to_track[stat] = current
            if goal is not None:
                goals_to_track[stat] = goal
                total_goal_sum += goal

    if not evs_to_track:
        await interaction.response.send_message(
            "❌ You must provide at least one EV to update.", ephemeral=True
        )
        return

    if total_goal_sum > MAX_TOTAL_EVS:
        await interaction.response.send_message(
            f"❌ Total EV goal ({total_goal_sum}) exceeds {MAX_TOTAL_EVS}.",
            ephemeral=True,
        )
        return

    # -------------------- Step 2: Determine Pokémon --------------------
    tracked = ev_tracker_cache.get(user_id)
    if not tracked:
        await interaction.response.send_message(
            "❌ You have no Pokémon currently being tracked. Use `/ev-tracker add` first.",
            ephemeral=True,
        )
        return

    pokemon_data = tracked
    pokemon_title = pokemon_data["pokemon"]
    dex_number = pokemon_data["dex_number"]

    # -------------------- Step 3: Save to database --------------------
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

        description_lines = [f"Updated **{pokemon_title} #{dex_number}** with new EVs:"]
        for stat, current in evs_to_track.items():
            goal = goals_to_track.get(stat)
            display_current = current if current is not None else "-"
            display_goal = goal if goal is not None else "-"
            description_lines.append(
                f"- {stat.upper()}: {display_current}/{display_goal}"
            )
        description_text = "\n".join(description_lines)

        embed = discord.Embed(
            title="EV Tracker Updated",
            description=description_text,
            color=0xFF99FF,
            timestamp=datetime.utcnow(),
        )
        embed = set_embed_user_context(embed, user)
        await load_ev_tracker_cache(bot)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        espeon_log(
            tag="sent",
            message=f"User {user_id} updated {pokemon_title} EVs: {evs_to_track} with goals {goals_to_track}",
            context=EspeonContext.STRAYMONS,
        )

        # -------------------- Step 4: Send log embed to staff --------------------
        staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
        if staff_channel:
            staff_embed = discord.Embed(
                title="EV Tracker Update",
                description=f"User **{user}** updated EVs for **{pokemon_title}**",
                color=0xAA66FF,
                timestamp=datetime.utcnow(),
            )
            for stat, current in evs_to_track.items():
                goal = goals_to_track.get(stat)
                display_current = current if current is not None else "-"
                display_goal = goal if goal is not None else "-"
                staff_embed.add_field(
                    name=stat.upper(),
                    value=f"{display_current}/{display_goal}",
                    inline=True,
                )
            await staff_channel.send(embed=staff_embed)

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to update EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await interaction.response.send_message(
            f"❌ Failed to update EVs: {e}", ephemeral=True
        )
