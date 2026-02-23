# -------------------- EV Tracker Battle Listener --------------------
import discord

from utils.cache.cache_list import ev_tracker_cache
from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.ev_tracker_embed import build_ev_tracker_embed
from utils.group_func.ev_tracker.ev_tracker_db_func import delete_tracked_ev
# enable_debug(f"{__name__}.handle_pokemeow_battle_message")
trainer_emoji = "<:trainer_brendan:1370001925092806706>"

EV_MAP = {
    "hp": {"trainer_name": "pie1_hp", "att_full": "HP"},
    "atk": {"trainer_name": "pie10_attack", "att_full": "Attack"},
    "spa": {"trainer_name": "pie2_specialattack", "att_full": "Sp. Attack"},
    "def": {"trainer_name": "pie3_defense", "att_full": "Defense"},
    "spd": {"trainer_name": "pie7_specialdefense", "att_full": "Sp. Defense"},
    "spe": {"trainer_name": "pie4_speed", "att_full": "Speed"},
}

# ✨───────────────────────────────────────────────✨
# 🪻 Handle Pokemeow Battle Message
# ✨───────────────────────────────────────────────✨


async def handle_pokemeow_battle_message(bot, message: discord.Message):
    """
    Listener for PokéMeow battle results.
    If user won and is tracking a mon, award EVs.
    Supports current/goal tracking.
    """

    if not message.embeds or not message.content:
        debug_log("No embeds or content in message. Exiting.")
        return

    content = message.content
    embed = message.embeds[0]
    title = embed.title or ""

    # 1. Check for "{username} won the battle"
    winner_name = None
    if "won the battle" in content:
        parts = content.split("**")
        if len(parts) >= 2:
            winner_name = parts[1].strip()
            debug_log(f"Detected winner: {winner_name}")
    if not winner_name:
        debug_log("No winner name found in message content. Exiting.")
        return

    # 2. Ensure user is in cache
    tracked = None
    for uid, data in ev_tracker_cache.items():
        if data.get("user_name") == winner_name:
            tracked = (uid, data)
            debug_log(f"User {winner_name} found in ev_tracker_cache with uid {uid}.")
            break

    if not tracked:
        debug_log(f"User {winner_name} not found in ev_tracker_cache. Exiting.")
        return

    user_id, tracked_data = tracked

    # -------------------- STEP 3: Dex number check --------------------

    lines = content.splitlines()
    xp_line = next((ln for ln in lines if "gained" in ln and "XP" in ln), None)
    if not xp_line:
        debug_log("No XP line found in message content. Exiting.")
        return

    # Check if emoji id is in the XP line, if not exit (means it's not the tracked mon)
    from utils.cache.ev_tracker_cache import get_emoji_id_cache

    dex_number = str(tracked_data.get("dex_number"))
    if not dex_number:
        debug_log("No dex_number found in tracked_data. Exiting.")
        return

    emoji_id = get_emoji_id_cache(user_id)
    if not emoji_id:
        debug_log("No emoji_id found in cache for user. Exiting.")
        # Ask user to do `;bud info dex`
        content = f"{winner_name}, I am missing your Pokémon's dex emoji to track EVs! Please do `;bud info {dex_number}` to let me know."
        await message.channel.send(content)
        return

    if not any(f"{emoji_id}" in xp_line for _ in [1]):
        debug_log(f"Emoji ID {emoji_id} not found in XP line. Exiting.")
        return

    # -------------------- STEP 4: Check tracked EVs --------------------

    tracked_evs = tracked_data.get("evs", {})
    tracked_goals = tracked_data.get("goals", {})
    if not tracked_evs:
        debug_log(f"No tracked EVs for user {winner_name}. Exiting.")
        return

    # -------------------- STEP 5: Award EVs (with goal cap) --------------------

    updated_evs = tracked_evs.copy()
    awarded_any = False

    for stat, info in EV_MAP.items():
        if stat in tracked_evs and info["trainer_name"] in title:
            goal = tracked_goals.get(stat)
            current = updated_evs.get(stat, 0)
            # Only award if under goal or if no goal
            if goal is None or current < goal:
                new_value = min(current + 9, goal) if goal is not None else current + 9
                debug_log(
                    f"Awarding 9 EVs to {winner_name} for stat {stat}: {current} -> {new_value} (goal: {goal})"
                )
                updated_evs[stat] = new_value
                awarded_any = True

    if not awarded_any:
        debug_log(f"No EVs awarded to {winner_name}. Exiting.")
        return

    # -------------------- STEP 6: Save updates --------------------

    try:
        await add_or_update_ev(
            bot=bot,
            user_id=user_id,
            user_name=winner_name,
            pokemon=tracked_data["pokemon"],
            dex_number=tracked_data.get("dex_number"),
            evs=updated_evs,
        )
        ev_tracker_cache[user_id]["evs"] = updated_evs

        debug_log(
            f"Successfully awarded EVs to {winner_name} ({tracked_data['pokemon']}): {updated_evs}"
        )
        espeon_log(
            tag="ev",
            message=f"Awarded EVs to {winner_name} ({tracked_data['pokemon']}): {updated_evs}",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        debug_log(f"Failed to award EVs to {winner_name}: {e}")
        espeon_log(
            tag="error",
            message=f"Failed to award EVs to {winner_name}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return

    # -------------------- STEP 7: Send summary embed --------------------
    embed, is_completed = await build_ev_tracker_embed(
        bot=bot,
        tracked_data=tracked_data,
        evs=updated_evs,
        goals=tracked_goals,
        guild=message.guild,
        user_id=user_id,
        title_prefix="💜 EV Tracker",
        summary_lines=None,
        use_progress_bar=False,
    )

    await message.channel.send(embed=embed)
    if is_completed:
        from utils.cache.ev_tracker_cache import get_ev_tracker, remove_ev_tracker_cache

        espeon_log(
            tag="ev",
            message=f"EV tracker completed for {winner_name} ({tracked_data['pokemon']})!",
            context=EspeonContext.STRAYMONS,
        )
        await delete_tracked_ev(bot, user_id)
        remove_ev_tracker_cache(user_id)
        espeon_log(
            tag="ev",
            message=f"EV tracker data deleted for {winner_name} ({tracked_data['pokemon']}) after completion.",
            context=EspeonContext.STRAYMONS,
        )
