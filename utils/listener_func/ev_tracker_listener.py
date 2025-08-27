# -------------------- EV Tracker Battle Listener --------------------
import discord
from utils.cache.ev_tracker_cache import ev_tracker_cache
from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.visuals.embeds.ev_tracker_embed import build_ev_tracker_embed

trainer_emoji = "<:trainer_brendan:1370001925092806706>"

EV_MAP = {
    "hp": {"trainer_name": "pie1_hp", "att_full": "HP"},
    "atk": {"trainer_name": "pie10_attack", "att_full": "Attack"},
    "spa": {"trainer_name": "pie2_specialattack", "att_full": "Sp. Attack"},
    "def": {"trainer_name": "pie3_defense", "att_full": "Defense"},
    "spd": {"trainer_name": "pie7_specialdefense", "att_full": "Sp. Defense"},
    "spe": {"trainer_name": "pie4_speed", "att_full": "Speed"},
}


async def handle_pokemeow_battle_message(bot, message: discord.Message):
    """
    Listener for PokéMeow battle results.
    If user won and is tracking a mon, award EVs.
    Supports current/goal tracking.
    """

    if not message.embeds or not message.content:
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
    if not winner_name:
        return

    # 2. Ensure user is in cache
    tracked = None
    for uid, data in ev_tracker_cache.items():
        print(f"[💙 DEBUG] Checking cache user -> {uid} ({data.get('user_name')})")
        if data.get("user_name") == winner_name:
            print(f"[🤍 MATCH] Winner {winner_name} found in cache (uid={uid})")
            tracked = (uid, data)
            break

    if not tracked:
        print(f"[💜 EXIT] No tracked EV entry found for {winner_name}, stopping here.")
        return

    user_id, tracked_data = tracked
    print(
        f"[💙 READY] Using tracked data for {winner_name} (uid={user_id}) -> {tracked_data}"
    )

    # -------------------- STEP 3: Dex number check --------------------
    lines = content.splitlines()
    xp_line = next((ln for ln in lines if "gained" in ln and "XP" in ln), None)
    if not xp_line:
        return

    dex_number = str(tracked_data.get("dex_number"))
    if not dex_number:
        return

    espeon_log(
        tag="debug",
        message=f"[STEP3] Winner={winner_name}, Dex={dex_number}, XP line='{xp_line}'",
        context=EspeonContext.STRAYMONS,
    )

    if not any(f":{dex_number}:" in xp_line for _ in [1]):
        espeon_log(
            tag="debug",
            message=f"[STEP3] Dex {dex_number} not found in XP line → exit",
            context=EspeonContext.STRAYMONS,
        )
        return
    espeon_log(
        tag="debug",
        message=f"[STEP3] Dex {dex_number} found in XP line → continue",
        context=EspeonContext.STRAYMONS,
    )

    # -------------------- STEP 4: Check tracked EVs --------------------
    tracked_evs = tracked_data.get("evs", {})
    tracked_goals = tracked_data.get(
        "goals", {}
    )  # expects { "hp": 252, "atk": 252, ... }
    espeon_log(
        tag="debug",
        message=f"[STEP4] Tracked EVs for {winner_name}: {tracked_evs}, Goals: {tracked_goals}",
        context=EspeonContext.STRAYMONS,
    )
    if not tracked_evs:
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
                # Cap the EV at the goal if it exists, otherwise just add 9
                new_value = min(current + 9, goal) if goal is not None else current + 9
                updated_evs[stat] = new_value
                awarded_any = True
                espeon_log(
                    tag="debug",
                    message=f"[STEP5] Matched trainer='{info['trainer_name']}' → +9 {stat.upper()} (capped at {goal})",
                    context=EspeonContext.STRAYMONS,
                )

    if not awarded_any:
        espeon_log(
            tag="debug",
            message=f"[STEP5] No matching EV type to award (all goals met) in title='{title}' → exit",
            context=EspeonContext.STRAYMONS,
        )
        return

    # -------------------- STEP 6: Save updates --------------------
    await add_or_update_ev(
        bot=bot,
        user_id=user_id,
        user_name=winner_name,
        pokemon=tracked_data["pokemon"],
        dex_number=tracked_data.get("dex_number"),
        evs=updated_evs,
    )
    ev_tracker_cache[user_id]["evs"] = updated_evs

    espeon_log(
        tag="ev",
        message=f"[STEP6] Awarded EVs to {winner_name} ({tracked_data['pokemon']}): {updated_evs}",
        context=EspeonContext.STRAYMONS,
    )

    # -------------------- STEP 7: Send summary embed --------------------
    embed = await build_ev_tracker_embed(
        bot=bot,
        tracked_data=tracked_data,
        evs=updated_evs,
        goals=tracked_goals,
        guild=message.guild,
        user_id=user_id,
        title_prefix="💜 EV Tracker",
        summary_lines=None,  # optional, e.g. for showing +9 updates if you want
        use_progress_bar=False,  # shows mini EV bars
    )

    await message.channel.send(embed=embed)
