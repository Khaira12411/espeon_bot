import re

import discord
from discord.ext import commands

from utils.cache.mr_weakness_cache import mr_weakness_user_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.weakness_embed import build_user_weakness_embed

# ─────────────────────────────────────────────
# Track last seen enemies **per user**
# ─────────────────────────────────────────────
_user_states: dict[int, dict] = {}  # user_id -> {"last_seen": [], "last_wave": None}
_user_active_enemy: dict[int, str] = {}  # user_id -> current active enemy


async def mr_weakness_chart(message: discord.Message, bot: commands.Bot):
    """
    Sends weakness embed only to the user who triggered/replied:
      - Only send an enemy once previous enemy has fainted.
      - Tracks sent enemies per wave and per user.
      - Respects user's cache: off/truncated/full.
    """
    # Only respond to the boss bot message
    if not message.author.bot or message.author.id != 664508672713424926:
        return

    # Must be a reply to a user
    if not message.reference or not message.reference.resolved:
        return
    target_user = message.reference.resolved.author
    user_id = target_user.id

    # Skip if user has Mr. Weakness off
    display_type = mr_weakness_user_cache.get(user_id, "full")
    if display_type == "off":
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

    # Gather all alive enemies in order
    alive_enemies = []
    for field in embed.fields:
        if "enemy" in field.name.lower() or "challenge" in field.name.lower():
            for line in field.value.splitlines():
                line = line.strip()
                if not line or "~~" in line:  # Skip fainted
                    continue

                candidate_enemy = line
                if challenge_type in ["elite", "death"]:
                    bold_match = re.search(r"\*\*(.+?)\*\*", line)
                    candidate_enemy = bold_match.group(1) if bold_match else line

                # Clean name
                candidate_enemy_clean = re.sub(
                    r"\*\*|<:.+?:\d+>|[\U00010000-\U0010ffff]", "", candidate_enemy
                )
                candidate_enemy_clean = re.sub(
                    r"\s+Lvl.*", "", candidate_enemy_clean, flags=re.IGNORECASE
                ).strip()

                if candidate_enemy_clean:
                    alive_enemies.append(candidate_enemy_clean)

    if not alive_enemies:
        espeon_log(
            tag="warn",
            message=f"No alive enemies found in embed '{title}'",
            context=EspeonContext.STRAYMONS,
        )
        return

    # ─────────────────────────────────────────────
    # Initialize per-user state
    # ─────────────────────────────────────────────
    if user_id not in _user_states:
        _user_states[user_id] = {"last_seen": [], "last_wave": None}

    user_state = _user_states[user_id]

    # Reset on new wave
    if current_wave != user_state["last_wave"]:
        user_state["last_seen"].clear()
        user_state["last_wave"] = current_wave
        _user_active_enemy.pop(user_id, None)  # Reset active enemy
        espeon_log(
            tag="ready",
            message=f"User {user_id}: New wave detected ({current_wave}), cleared last_seen",
            context=EspeonContext.STRAYMONS,
        )

    # ─────────────────────────────────────────────
    # Determine current active enemy
    # ─────────────────────────────────────────────
    current_enemy = _user_active_enemy.get(user_id)
    if current_enemy not in alive_enemies:
        # Previous enemy fainted or first enemy
        current_enemy = alive_enemies[0]
        _user_active_enemy[user_id] = current_enemy
        espeon_log(
            tag="ready",
            message=f"User {user_id}: Now facing {current_enemy}",
            context=EspeonContext.STRAYMONS,
        )
    else:
        # Still facing the same enemy; do not advance
        espeon_log(
            tag="skip",
            message=f"User {user_id}: Still facing {current_enemy}, embed not sent until it faints",
            context=EspeonContext.STRAYMONS,
        )
        return

    # Build and send embed in the same channel
    try:
        embed_to_send = build_user_weakness_embed(
            current_enemy, user_id, mr_weakness_user_cache
        )
        if embed_to_send:
            await message.channel.send(embed=embed_to_send)
            espeon_log(
                tag="sent",
                message=f"User {user_id}: Sent weakness embed for {current_enemy}",
                context=EspeonContext.STRAYMONS,
            )
        else:
            espeon_log(
                tag="warn",
                message=f"User {user_id}: Could not build embed for {current_enemy}",
                context=EspeonContext.STRAYMONS,
            )
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to send Mr. Weakness embed to user {user_id} for {current_enemy}: {e}",
            context=EspeonContext.STRAYMONS,
        )
