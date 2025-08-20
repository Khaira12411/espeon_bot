import re

import discord

_last_enemy_seen = []  # Tracks the order of enemies we’ve sent embeds for
_last_wave_number = None

from utils.visuals.embeds.weakness_embed import build_weakness_embed_from_input


async def mr_weakness_chart(message: discord.Message):
    """
    Sends weakness embeds sequentially for current enemies:
    - Only send an enemy once the previous one has fainted.
    - Tracks sent enemies per wave; resets on new wave or battle restart.
    """
    global _last_enemy_seen, _last_wave_number

    if not message.author.bot or message.author.id != 664508672713424926:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]
    title = embed.title or ""

    # Detect wave number
    wave_match = re.search(r"wave\s*(\d+)", title, flags=re.IGNORECASE)
    current_wave = int(wave_match.group(1)) if wave_match else None

    # Reset on new wave or battle restart
    if current_wave != _last_wave_number or current_wave is None:
        _last_enemy_seen.clear()
        _last_wave_number = current_wave
        print(f"[🫐 DEBUG] New wave or battle reset detected. Clearing sent enemies.")

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

                if challenge_type in ["elite", "death"]:
                    bold_match = re.search(r"\*\*(.+?)\*\*", line)
                    candidate_enemy = bold_match.group(1) if bold_match else line
                else:
                    candidate_enemy = line

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
        print("[🫐 DEBUG] No alive enemies found.")
        return

    # Decide which enemy to send next
    next_enemy_to_send = None

    if not _last_enemy_seen:
        # First enemy: send first in list
        next_enemy_to_send = alive_enemies[0]
    else:
        # Send next only if previous enemy has fainted
        for i, enemy in enumerate(_last_enemy_seen):
            if enemy in alive_enemies:
                # Previous enemy still alive: wait
                next_enemy_to_send = None
                break
        else:
            # Previous enemies have all fainted, send first unsent alive
            for enemy in alive_enemies:
                if enemy not in _last_enemy_seen:
                    next_enemy_to_send = enemy
                    break

    if not next_enemy_to_send:
        print("[🫐 DEBUG] No new enemy ready to send yet (previous not fainted).")
        return

    _last_enemy_seen.append(next_enemy_to_send)
    print(f"[🫐 DEBUG] Sending weakness embed for: {next_enemy_to_send}")

    try:
        embed_to_send = build_weakness_embed_from_input(next_enemy_to_send)
        if embed_to_send:
            await message.channel.send(embed=embed_to_send)
        else:
            print(f"[💣 ERROR] Could not build embed for {next_enemy_to_send}")
    except Exception as e:
        print(f"[💣 ERROR] Failed to send weakness embed: {e}")
