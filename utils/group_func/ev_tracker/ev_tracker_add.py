# 🟣────────────────────────────────────────────
#           💜 EV Tracker Brain: Track 💜
# 🟣────────────────────────────────────────────
from datetime import datetime

import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import ev_tracker_cache
from utils.database.server_shop import format_item_name
from utils.essentials.loader import pretty_defer
from utils.function.webhook import send_webhook
from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.group_func.market_alert.parsers import (
    parse_special_mega_input,
    resolve_pokemon_input,
)
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed

STAFF_LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.server_logs

MAX_EVS_PER_STAT = 252
MAX_TOTAL_EVS = 510

# 🟣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   💜 Espeon Helper Function › Build EV Lines 💜
# 🟣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def build_ev_lines(evs_to_track: dict, goals_to_track: dict) -> list[str]:
    """Builds formatted EV lines for a Pokemon."""
    lines = []
    for stat, current in evs_to_track.items():
        goal = goals_to_track.get(stat)
        if goal is not None:
            lines.append(f"- {stat.upper()}: {current}/{goal}")
        else:
            lines.append(f"- {stat.upper()}: {current}")
    return lines


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › EV Tracker Add ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def ev_tracker_add_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
    hp=None,
    atk=None,
    spa=None,
    def_=None,
    spd=None,
    spe=None,
):
    from utils.cache.ev_tracker_cache import load_ev_tracker_cache

    emoji_id = None
    user = interaction.user
    user_id = user.id

    # 💜 Start loader
    handle = await pretty_defer(interaction, content="Tracking your EVs...")

    # ✨──────── Step 1 › Collect EV stats with goals ─────✨
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

            if "/" not in val_str:
                await handle.error(
                    content=f"Invalid format for **{stat.upper()}**. Use `current/goal` (e.g., 0/252)."
                )
                return

            parts = val_str.split("/")
            try:
                current = int(parts[0].strip())
                goal = int(parts[1].strip()) if len(parts) > 1 else None
            except ValueError:
                await handle.error(
                    content=f"Invalid number for **{stat.upper()}**. Use integers only (e.g., 0/252)."
                )
                return

            if goal is not None and goal > MAX_EVS_PER_STAT:
                await handle.error(
                    content=f"The goal for **{stat.upper()}** cannot exceed {MAX_EVS_PER_STAT}."
                )
                return

            evs_to_track[stat] = current
            if goal is not None:
                goals_to_track[stat] = goal
                total_goal_sum += goal

    if not evs_to_track:
        await handle.error(content="You must provide at least one EV to track.")
        return

    if total_goal_sum > MAX_TOTAL_EVS:
        await handle.error(
            content=f"The total sum of your EV goals ({total_goal_sum}) exceeds {MAX_TOTAL_EVS}."
        )
        return

    # ✨──────── Step 2 › Resolve Pokemon ─────✨
    pokemon_title = pokemon.title()
    try:
        if pokemon.isdigit():
            if len(pokemon) == 4 and not pokemon.startswith(("1", "7", "9")):
                raise ValueError("Invalid 4-digit Dex number.")
            pokemon, dex_number = resolve_pokemon_input(pokemon)
            pokemon_title = pokemon.title()
        elif any(
            (
                pokemon_title.startswith(f"{prefix}Mega ")
                or pokemon_title.startswith(f"{prefix}Mega-")
            )
            for prefix in ["", "Shiny ", "Golden "]
        ):
            dex_number = parse_special_mega_input(pokemon)
            pokemon = pokemon_title
        else:
            pokemon, dex_number = resolve_pokemon_input(pokemon)
    except Exception as e:
        espeon_log(
            "critical",
            f"Failed to resolve Pokemon: {e}",
            source="EVTracker",
            exc=e,
            include_trace=True,
        )
        await handle.error(content=f"Could not resolve Pokemon '{pokemon}': {e}")
        return

    # ✨──────── Step 3 › Save to Database ─────✨
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

        # 💜 Insert/update cache instead of full reload
        from utils.cache.ev_tracker_cache import insert_ev_tracker_cache

        insert_ev_tracker_cache(
            {
                "user_id": user_id,
                "user_name": user.name,
                "pokemon": pokemon_title,
                "emoji_id": emoji_id,
                "dex_number": dex_number,
                **evs_to_track,
                **{f"{k}_goal": v for k, v in goals_to_track.items()},
            }
        )

        # ✨──────── Step 4 › Build Confirmation Embed ─────✨
        user_desc_lines = [
            f"- **Pokemon:** {pokemon_title} #{dex_number}\n{Espeon_Emoji.purple_pie} **EVs:**"
        ]
        user_desc_lines.extend(build_ev_lines(evs_to_track, goals_to_track))

        embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_star} EV Tracker Started",
            description="\n".join(user_desc_lines),
            color=0xFF99FF,
        )
        embed = design_embed(embed=embed, user=user, pokemon_name=pokemon_title)

        await handle.success(
            embed=embed,
            content=f"Kindly do `;bud info {dex_number}` to let me know your Pokémon's dex emoji for tracking EVs!",
        )

        espeon_log(
            tag="sent",
            message=f"User {user.name} started tracking {pokemon_title} EVs: {evs_to_track} with goals {goals_to_track}",
            context=EspeonContext.STRAYMONS,
        )
        formatted_name = format_item_name(pokemon_title, dex=dex_number)

        # ✨──────── Step 5 › Send Staff Log Embed ─────✨
        staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
        if staff_channel:
            staff_desc_lines = [
                f"- **Member:** {user.mention}\n- **Pokemon:** {formatted_name}\n{Espeon_Emoji.purple_pie} **EVs:**"
            ]
            staff_desc_lines.extend(build_ev_lines(evs_to_track, goals_to_track))

            staff_embed = discord.Embed(
                title=f"{Espeon_Emoji.purple_star} EV Tracker Added",
                description="\n".join(staff_desc_lines),
                color=0xFF99FF,
                timestamp=datetime.now(),
            )
            staff_embed = design_embed(
                embed=staff_embed, user=user, pokemon_name=pokemon_title
            )

            await send_webhook(
                bot=bot,
                channel=staff_channel,
                embed=staff_embed,
            )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to track EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await handle.error(content=f"Failed to track EVs: {e}")
