# 🟣────────────────────────────────────────────
#           💜 EV Tracker Brain: Track 💜
# 🟣────────────────────────────────────────────
from datetime import datetime

import discord

from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.group_func.market_alert.parsers import (
    parse_special_mega_input,
    resolve_pokemon_input,
)
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import set_embed_user_context

MAX_EVS_PER_STAT = 252
MAX_TOTAL_EVS = 510


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
    from utils.cache.ev_tracker_cache import ev_tracker_cache, load_ev_tracker_cache

    user = interaction.user
    user_id = user.id

    # -------------------- Step 1: Collect EV stats with goals --------------------
    evs_to_track = {}
    goals_to_track = {}
    total_goal_sum = 0  # ✅ initialize here

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

            # Validate current/goal format
            if "/" not in val_str:
                await interaction.response.send_message(
                    f"❌ Invalid format for **{stat.upper()}**. "
                    f"Please provide as `current/goal` (e.g., 0/252).",
                    ephemeral=True,
                )
                return

            # Split and convert to int
            parts = val_str.split("/")
            try:
                current = int(parts[0].strip())
                goal = int(parts[1].strip()) if len(parts) > 1 else None
            except ValueError:
                await interaction.response.send_message(
                    f"❌ Invalid number for **{stat.upper()}**. "
                    f"Please provide integers only, e.g., 0/252.",
                    ephemeral=True,
                )
                return
            # ✅ Validate per-stat max
            if goal is not None and goal > MAX_EVS_PER_STAT:
                await interaction.response.send_message(
                    f"❌ The goal for **{stat.upper()}** cannot exceed {MAX_EVS_PER_STAT}.",
                    ephemeral=True,
                )
                return
            evs_to_track[stat] = current
            if goal is not None:
                goals_to_track[stat] = goal
                total_goal_sum += goal
    if not evs_to_track:
        await interaction.response.send_message(
            "❌ You must provide at least one EV to track.", ephemeral=True
        )
        return

    # ✅ Validate total EV max
    if total_goal_sum > MAX_TOTAL_EVS:
        await interaction.response.send_message(
            f"❌ The total sum of your EV goals ({total_goal_sum}) exceeds the "
            f"maximum allowed total of {MAX_TOTAL_EVS}.",
            ephemeral=True,
        )
        return

    # -------------------- Step 2: Resolve Pokémon --------------------
    pokemon_title = pokemon.title()
    try:
        if pokemon.isdigit():
            if len(pokemon) == 4 and not pokemon.startswith(("1", "7", "9")):
                raise ValueError("Invalid 4-digit Dex number.")
            pokemon, dex_number = resolve_pokemon_input(pokemon)
            pokemon_title = pokemon.title()
        elif any(
            pokemon_title.startswith(f"{prefix}Mega ")
            for prefix in ["", "Shiny ", "Golden "]
        ):
            dex_number = parse_special_mega_input(pokemon)
            pokemon = pokemon_title
        else:
            pokemon, dex_number = resolve_pokemon_input(pokemon)
    except Exception as e:
        espeon_log(
            "critical",
            f"Failed to resolve Pokémon: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.response.send_message(
            f"❌ Could not resolve Pokémon '{pokemon}': {e}", ephemeral=True
        )
        return

    # -------------------- Step 3: Save to database --------------------
    try:
        await add_or_update_ev(
            bot,
            user_id,
            user.name,  # user_name
            pokemon_title,  # pokemon
            evs_to_track,  # current EVs
            goals=goals_to_track,  # goal EVs
            dex_number=dex_number,
        )

        # -------------------- Step 4: Build confirmation embed --------------------
        description_lines = [
            f"Tracking **{pokemon_title} #{dex_number}** with the following EVs:"
        ]
        for stat, current in evs_to_track.items():
            goal = goals_to_track.get(stat)
            if goal is not None:
                description_lines.append(f"- {stat.upper()}: {current}/{goal}")
            else:
                description_lines.append(f"- {stat.upper()}: {current}")

        description_text = "\n".join(description_lines)

        embed = discord.Embed(
            title="EV Tracker Started",
            description=description_text,
            color=0xFF99FF,
            timestamp=datetime.utcnow(),
        )
        embed = set_embed_user_context(embed, user)

        # 💜 Load EV Tracker cache
        await load_ev_tracker_cache(bot)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        espeon_log(
            tag="sent",
            message=f"User {user_id} started tracking {pokemon_title} EVs: {evs_to_track} with goals {goals_to_track}",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to track EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await interaction.response.send_message(
            f"❌ Failed to track EVs: {e}", ephemeral=True
        )
