import re

import discord
from discord.ext import commands

from utils.cache.cache_list import mr_weakness_user_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.weakness_embed import build_user_weakness_embed
from utils.essentials.pokemon_reply import get_pokemeow_reply_member

# ─────────────────────────────────────────────
# Track last seen enemies per user
# ─────────────────────────────────────────────
_user_states: dict[int, dict] = {}  # user_id -> {"last_seen": [], "last_wave": None}
_user_active_enemy: dict[int, str] = {}  # user_id -> current active enemy


# ✨───────────────────────────────────────────────✨
# 🪻 MR Weakness Chart
# ✨───────────────────────────────────────────────✨
async def mr_weakness_chart(message: discord.Message, bot: commands.Bot):
    """
    Sends weakness embed only to the user who triggered/replied:
      - Tracks sent enemies per wave and per user.
      - Respects user's cache: off/truncated/full.
    """
    # Only respond to the boss bot message
    if not message.author.bot or message.author.id != 664508672713424926:
        return

    # Must be a reply to a user
    target_user = await get_pokemeow_reply_member(message)
    if not target_user:
        return

    user_id = target_user.id

    # EARLY CHECK: Skip if user has Mr. Weakness off (before any processing)
    display_type = mr_weakness_user_cache.get(
        user_id, "off"
    )  # Default to "off" if not in cache
    if display_type.lower() == "off":
        # Clean up any existing state for this user when it's turned off
        _user_states.pop(user_id, None)
        _user_active_enemy.pop(user_id, None)
        return

    if not message.embeds:
        return

    embed = message.embeds[0]
    title = embed.title or ""

    # Detect wave number
    wave_match = re.search(r"wave\s*(\d+)", title, flags=re.IGNORECASE)
    current_wave = int(wave_match.group(1)) if wave_match else None

    # Determine challenge type
    challenge_type = "normal"
    if "elite challenge" in title.lower():
        challenge_type = "elite"
    elif "death challenge" in title.lower():
        challenge_type = "death"

    # Gather alive enemies
    alive_enemies = []
    for field in embed.fields:
        if (
            "enemy" in field.name.lower()
            or "challenge" in field.name.lower()
            and not "mega" in field.name.lower()
        ):
            for line in field.value.splitlines():
                line = line.strip()
                if not line or "~~" in line:
                    continue

                candidate_enemy = line
                if challenge_type in ["elite", "death"]:
                    bold_match = re.search(r"\*\*(.+?)\*\*", line)
                    candidate_enemy = bold_match.group(1) if bold_match else line

                candidate_enemy_clean = re.sub(
                    r"\*\*|<:.+?:\d+>|[\U00010000-\U0010ffff]", "", candidate_enemy
                )
                candidate_enemy_clean = re.sub(
                    r"\s+Lvl.*", "", candidate_enemy_clean, flags=re.IGNORECASE
                ).strip()

                if candidate_enemy_clean:
                    alive_enemies.append(candidate_enemy_clean)

    if not alive_enemies:
        return

    # Initialize per-user state
    if user_id not in _user_states:
        _user_states[user_id] = {"last_seen": [], "last_wave": None}

    user_state = _user_states[user_id]

    # Reset on new wave
    if current_wave != user_state["last_wave"]:
        user_state["last_seen"].clear()
        user_state["last_wave"] = current_wave
        _user_active_enemy.pop(user_id, None)

    # Determine current active enemy
    current_enemy = _user_active_enemy.get(user_id)
    if current_enemy not in alive_enemies:
        current_enemy = alive_enemies[0]
        _user_active_enemy[user_id] = current_enemy
    else:
        # Still facing the same enemy; do not advance
        return

    # Build and send embed
    try:
        embed_to_send = build_user_weakness_embed(
            current_enemy, user_id, mr_weakness_user_cache
        )
        if embed_to_send:
            await message.channel.send(embed=embed_to_send)
        else:
            espeon_log(
                tag="warn",
                message=f"User {user_id}: Could not build embed for {current_enemy}",
                context=EspeonContext.STRAYMONS,
            )
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to send Mr. Weakness embed to {target_user.display_name} for {current_enemy}: {e}",
            context=EspeonContext.STRAYMONS,
        )
