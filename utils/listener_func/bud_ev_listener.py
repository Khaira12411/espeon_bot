# -------------------- EV Tracker Embed Sync Listener --------------------
import re

import discord

from config.aesthetic import Espeon_Emoji
from utils.cache.cache_list import ev_tracker_cache
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.group_func.ev_tracker.ev_tracker_db_func import (
    add_or_update_ev,
    update_emoji_id,
)
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.ev_tracker_embed import build_ev_tracker_embed

# enable_debug(f"{__name__}.handle_pokemeow_embed_sync")


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › EV Tracker Embed Sync Handler ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

    embed = message.embeds[0]
    title = embed.title or ""

    user = await get_pokemeow_reply_member(message)
    if not user:
        debug_log("No user found in message reply. Exiting.")
        return

    user_id = user.id

    # Check if user is in EV tracker cache
    user_ev_data = ev_tracker_cache.get(user_id)
    if not user_ev_data:
        debug_log(f"User id {user_id} not found in ev_tracker_cache. Exiting.")
        return

    # -------------------- STEP 1: Extract username, dex emoji, and pokemon name --------------------
    # Updated regex: only match the emoji immediately after the username as the Pokémon emoji
    match = re.match(
        r"(<:\w+:(\d+)>) (\S+)'s (<:\w+:(\d+)>)(?: [^\w<]*)? ([\w\-'.]+)", title
    )
    if not match:
        debug_log(f"Title did not match expected pattern: {title!r}. Exiting.")
        return
    (
        user_battle_icon_tag,
        user_battle_icon_id,
        user_name,
        pokemon_emoji_tag,
        pokemon_emoji_id,
        pokemon_name,
    ) = match.groups()
    debug_log(
        f"Parsed from embed title: user_battle_icon_tag={user_battle_icon_tag}, user_battle_icon_id={user_battle_icon_id}, user_name={user_name}, pokemon_emoji_tag={pokemon_emoji_tag}, pokemon_emoji_id={pokemon_emoji_id}, pokemon_name={pokemon_name}"
    )
    from utils.cache.ev_tracker_cache import get_emoji_id_cache

    tracked_pokemon_name = user_ev_data.get("pokemon", "").lower()

    if tracked_pokemon_name == pokemon_name.lower():
        debug_log(
            f"Pokemon name mismatch: tracked={tracked_pokemon_name}, embed={pokemon_name.lower()}. Exiting."
        )
        old_emoji_id = get_emoji_id_cache(user_id)
        if old_emoji_id != pokemon_emoji_tag:
            debug_log(f"Emoji ID mismatch for user {user_name} (id: {user_id}")
            debug_log(
                f"Old emoji_id: {old_emoji_id}, New emoji_id from embed: {pokemon_emoji_tag}"
            )
            try:
                await update_emoji_id(bot, user_id, pokemon_emoji_tag)
                await message.add_reaction(Espeon_Emoji.purple_check)
            except Exception as e:
                espeon_log(
                    tag="error",
                    message=f"Failed to update emoji_id for user {user_id} in DB: {e}",
                    context=EspeonContext.STRAYMONS,
                )
                debug_log(f"Failed to update emoji_id for user {user_id} in DB: {e}")
                
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
        debug_log(
            f"User {user_name} not found in ev_tracker_cache by user_name. Exiting."
        )
        return
    user_id, tracked_data = tracked

    # -------------------- STEP 3: Verify both dex_number and pokemon name match --------------------

    # Check if pokemon names match (case-insensitive)
    tracked_pokemon = tracked_data.get("pokemon", "").lower()
    if tracked_pokemon != pokemon_name.lower():
        debug_log(
            f"Pokemon name mismatch: tracked={tracked_pokemon}, embed={pokemon_name.lower()}. Exiting."
        )
        # Check if emoji id matches as a fallback (handles cases where user might have changed tracked Pokémon but embed is still old one)
        tracked_emoji_id = tracked_data.get("emoji_id")
        if tracked_emoji_id != pokemon_emoji_tag:
            debug_log(
                f"Emoji ID mismatch as well: tracked={tracked_emoji_id}, embed={pokemon_emoji_tag}. Exiting."
            )
            return

    # -------------------- STEP 4: Extract Pokemon EVs field --------------------
    # Find the index of the field with 'Pokémon EVs' in the name
    ev_field_values = []
    ev_field_index = None
    for idx, f in enumerate(embed.fields):
        if "Pokémon EVs" in f.name:
            ev_field_index = idx
            break

    if ev_field_index is not None:
        # Always include the 'Pokémon EVs' field
        ev_field_values.append(embed.fields[ev_field_index].value)
        # Include all immediately following fields with empty or whitespace-only names
        for f in embed.fields[ev_field_index + 1 :]:
            # Handle truly empty, whitespace-only, or zero-width space names
            if not f.name or f.name.strip() == "" or f.name.strip() == "​":
                ev_field_values.append(f.value)
            else:
                break

    # Join everything into one string before regex
    ev_text = " ".join(ev_field_values)
    debug_log(f"Combined EV text: {ev_text!r}")

    # Robust regex: handles optional backticks, bold markers, and odd spacing
    ev_matches = re.findall(
        r"`?\s*(ATK|DEF|HP|SPE|SPA|SPD)\s*`?\s*\**\s*(\d+)\s*\**", ev_text
    )
    debug_log(f"Regex EV matches: {ev_matches}")

    parsed_evs = {k.lower(): int(v) for k, v in ev_matches}
    debug_log(f"Parsed EVs from embed: {parsed_evs}")

    # -------------------- STEP 5: Compare and update tracked EVs --------------------

    tracked_evs = tracked_data.get("evs", {})
    tracked_stats = [
        s for s in ["hp", "atk", "spa", "def", "spd", "spe"] if s in tracked_evs
    ]
    debug_log(f"Tracked EVs: {tracked_evs}")
    debug_log(f"Tracked stats: {tracked_stats}")
    old_values = {stat: tracked_evs[stat] for stat in tracked_stats}
    summary_lines = []
    updated = False

    for stat in tracked_stats:
        new_val = parsed_evs.get(stat, tracked_evs[stat])
        if tracked_evs[stat] != new_val:
            debug_log(
                f"Updating {stat} for {user_name}: {tracked_evs[stat]} -> {new_val}"
            )
            summary_lines.append(f"{stat.upper()}: {tracked_evs[stat]} → {new_val}")
            tracked_evs[stat] = new_val
            updated = True

    if not updated:
        debug_log(f"No EVs updated for {user_name}. Exiting.")
        return

    # Save to DB and cache
    try:
        await add_or_update_ev(
            bot=bot,
            user_id=user_id,
            user_name=tracked_data["user_name"],
            pokemon=tracked_data["pokemon"],
            dex_number=tracked_data.get("dex_number"),
            evs=tracked_evs,
        )
        ev_tracker_cache[user_id]["evs"] = tracked_evs
        debug_log(f"Successfully updated EVs for {user_name}: {tracked_evs}")
    except Exception as e:
        debug_log(f"Failed to update EVs for {user_name}: {e}")
        return

    # -------------------- STEP 6: Send confirmation embed with summary --------------------
    embed, is_completed = await build_ev_tracker_embed(
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
