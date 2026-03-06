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
from utils.function.pokemon_func import get_display_name
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed
from utils.database.market_value_db import fetch_emoji_id_cache, fetch_emoji_id_db
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
    # 💜 Determine target_name and dex_number
    espeon_log(
        tag="debug",
        message=f"Resolving Pokemon input: {pokemon_title}",
        context=EspeonContext.STRAYMONS,
    )
    target_name, display_name, dex_number, error = resolve_pokemon_input(
        pokemon_title
    )
    debug_log(
        f"Resolved: target_name={target_name}, display_name={display_name}, dex_number={dex_number}, error={error}"
    )
    if error:
        debug_log(f"Error resolving pokemon: {error}")
        await handle.error(content=error)
        return

    # Fetch emoji ID from cache
    emoji_id = fetch_emoji_id_cache(pokemon_title)
    if not emoji_id:
        # Fetch from DB as fallback
        emoji_id = await fetch_emoji_id_db(bot, pokemon_title)

    has_emoji = False if emoji_id is None else True

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
            emoji_id=emoji_id,
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
                "emoji_id": emoji_id,
                **evs_to_track,
                **{f"{k}_goal": v for k, v in goals_to_track.items()},
            }
        )

        # ✨──────── Step 4 › Build Confirmation Embed ─────✨
        display_formatted_name = get_display_name(pokemon_title, dex=dex_number)
        user_desc_lines = [
            f"- **Pokemon:** {display_formatted_name}\n{Espeon_Emoji.purple_pie} **EVs:**"
        ]
        user_desc_lines.extend(build_ev_lines(evs_to_track, goals_to_track))

        embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_star} EV Tracker Started",
            description="\n".join(user_desc_lines),
            color=0xFF99FF,
        )

        embed = design_embed(embed=embed, user=user, pokemon_name=pokemon_title)
        content = None if has_emoji else f"Kindly do `;bud info {dex_number}` to let me know your Pokémon's dex emoji for tracking EVs!"
        await handle.success(
            embed=embed,
            content=content,
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
                f"- **Member:** {user.mention}\n- **Pokemon:** {display_formatted_name}\n{Espeon_Emoji.purple_pie} **EVs:**"
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
