# -------------------- EV Tracker Embed Sync Listener --------------------
import discord
import re
from utils.cache.ev_tracker_cache import ev_tracker_cache
from utils.group_func.ev_tracker.ev_tracker_db_func import add_or_update_ev
from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.visuals.embeds.ev_tracker_embed import build_ev_tracker_embed


async def handle_pokemeow_embed_sync(bot, message: discord.Message):
    """
    Listener for syncing EVs from PokéMeow embeds.
    Only triggers if the message:
        - is from PokéMeow
        - has an embed
        - is a reply to someone
    Updates tracked EVs in database and cache if they differ from the embed.
    Only updates stats the user is tracking.
    """

    # Must be from a bot, have an embed, and be a reply
    if not message.author.bot or not message.embeds or not message.reference:
        return

    embed = message.embeds[0]
    title = embed.title or ""

    # -------------------- STEP 1: Extract username and dex emoji --------------------
    match = re.match(r"<:.*?:\d+> (\S+)'s <:([0-9]+):\d+> .*", title)
    if not match:
        return
    user_name, dex_emoji_name = match.groups()

    # -------------------- STEP 2: Check if user is in EV tracker cache --------------------
    tracked = next(
        (
            (uid, data)
            for uid, data in ev_tracker_cache.items()
            if data.get("user_name") == user_name
        ),
        None,
    )
    if not tracked:
        return
    user_id, tracked_data = tracked

    # Optional: verify dex_number matches
    if str(tracked_data.get("dex_number")) != dex_emoji_name:
        return

    # -------------------- STEP 3: Extract Pokémon EVs field --------------------
    ev_field = next((f for f in embed.fields if "Pokémon EVs" in f.name), None)
    if not ev_field:
        return

    parsed_evs = {
        m.group(1).lower(): int(m.group(2))
        for m in re.finditer(r"`([A-Z]+)`\s*(\d+)", ev_field.value)
    }

    # -------------------- STEP 4: Compare and update tracked EVs --------------------
    tracked_evs = tracked_data.get("evs", {})
    tracked_stats = [
        s for s in ["hp", "atk", "spa", "def", "spd", "spe"] if s in tracked_evs
    ]
    old_values = {stat: tracked_evs[stat] for stat in tracked_stats}
    summary_lines = []
    updated = False

    for stat in tracked_stats:
        new_val = parsed_evs.get(stat, tracked_evs[stat])
        if tracked_evs[stat] != new_val:
            summary_lines.append(f"{stat.upper()}: {tracked_evs[stat]} → {new_val}")
            tracked_evs[stat] = new_val
            updated = True

    if not updated:
        print("[💜 STEP4] No updates needed → exit")
        return

    # Save to DB and cache
    await add_or_update_ev(
        bot=bot,
        user_id=user_id,
        user_name=tracked_data["user_name"],
        pokemon=tracked_data["pokemon"],
        dex_number=tracked_data.get("dex_number"),
        evs=tracked_evs,
    )
    ev_tracker_cache[user_id]["evs"] = tracked_evs

    # -------------------- STEP 5: Send confirmation embed with summary --------------------
    embed = await build_ev_tracker_embed(
        bot=bot,
        tracked_data=tracked_data,
        evs=tracked_evs,
        goals=tracked_data.get("goals", {}),
        guild=message.guild,
        user_id=user_id,
        title_prefix="💜 EV Tracker Synced",
        summary_lines=summary_lines,  # pass in the changes for the field
        use_progress_bar=False,  # optional, mini bars not necessary here
    )

    await message.channel.send(embed=embed)
