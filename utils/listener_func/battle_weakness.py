import asyncio
import re

import discord
from discord.ext import commands

from utils.cache.cache_list import (
    not_weakness_chart_user_names,
    processed_weakness_messages,
)
from utils.cache.mr_weakness_cache import (
    get_display_type_via_user_id,
    get_display_type_via_user_name,
)
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.group_func.mr_weakness.mr_weakness_db_func import update_user_name
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.weakness_embed import build_user_weakness_embed_w_o_cache

#enable_debug(f"{__name__}.weakness_chart")


async def _retry_discord_send(send_func, *, retries: int = 3, delay: float = 1.5):
    """
    Retry transient Discord send failures (5xx / 429) a few times.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return await send_func()
        except discord.HTTPException as e:
            last_error = e
            if e.status in {429, 500, 502, 503, 504}:
                if attempt < retries:
                    await asyncio.sleep(delay)
                    continue
            raise

    if last_error:
        raise last_error


def extract_name_before_vs(title: str) -> tuple[str | None, str | None]:
    """
    Extract user and enemy names from a battle title.

    Example:
      ':crossed_swords: <:beauty:123>hana_banana._ vs. <:gym:456>Leader Brock'
      -> ('hana_banana._', 'Leader Brock')
    """
    if not title:
        return None, None

    # Split once on 'vs' / 'vs.' to isolate each side.
    parts = re.split(r"\s+vs\.?\s+", title, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None, None

    left_side, right_side = parts[0], parts[1]

    # User name: text after the last emoji marker '>' on the left side.
    user_matches = re.findall(r"(?:^|>)\s*([^<>\n]+)$", left_side.strip())
    user_name = user_matches[-1].strip() if user_matches else None

    # Enemy name: remove leading emoji blocks and trailing spaces.
    enemy_name = re.sub(r"^(?:<:[^:>]+:\d+>\s*)+", "", right_side).strip()
    if not enemy_name:
        enemy_name = None

    return user_name, enemy_name


def _format_enemy_name_from_line(line: str) -> str | None:
    """
    Extract enemy name from a line and prepend Golden/Shiny when present.

    Example line:
      '<:74_:722260568399937568> **Geodude** HP 228/228'
    """
    if not line:
        return None

    # Prefer bold text in the line.
    bold_match = re.search(r"\*\*(.+?)\*\*", line)
    if bold_match:
        base_name = bold_match.group(1).strip()
    else:
        no_emoji = re.sub(r"<:[^:>]+:\d+>", "", line)
        before_hp = re.split(r"\bHP\b", no_emoji, maxsplit=1, flags=re.IGNORECASE)[0]
        base_name = before_hp.strip(" -:\t")

    if not base_name:
        return None

    line_lower = line.lower()
    if "golden" in line_lower and not base_name.lower().startswith("golden "):
        base_name = f"Golden {base_name}"
    elif "shiny" in line_lower and not base_name.lower().startswith("shiny "):
        base_name = f"Shiny {base_name}"

    return base_name


def extract_enemy_pokemon_from_embed(embed: discord.Embed) -> str | None:
    """
    Extract the currently shown enemy Pokemon from battle embed fields.
    Returns the first line with bold text (**) from enemy/team fields.
    """
    if not embed or not embed.fields:
        return None

    player_name, _enemy_name_from_title = extract_name_before_vs(embed.title or "")

    def is_enemy_side_field(field_obj) -> bool:
        field_name_raw = field_obj.name or ""
        field_name = field_name_raw.lower()

        if "enemy" in field_name:
            return True

        if "team" in field_name:
            if player_name and player_name.lower() in field_name:
                return False
            return True

        return False

    candidate_fields = [f for f in embed.fields if is_enemy_side_field(f)]
    if not candidate_fields:
        return None

    for field in candidate_fields:
        field_name = (field.name or "").lower()
        if "enemy" not in field_name and "team" not in field_name:
            continue

        for raw_line in (field.value or "").splitlines():
            line = raw_line.strip()
            if not line or "~~" in line:
                continue

            # Prefer active line that contains **Pokemon** formatting.
            if "**" in line:
                parsed = _format_enemy_name_from_line(line)
                if parsed:
                    return parsed

        # Fallback: first non-empty line in case bold was missing.
        for raw_line in (field.value or "").splitlines():
            line = raw_line.strip()
            if not line or "~~" in line:
                continue

            parsed = _format_enemy_name_from_line(line)
            if parsed:
                return parsed

    return None


def extract_npc_wins_from_footer(embed: discord.Embed) -> int | None:
    """
    Extract wins from footer text like:
      'Your wins against NPC 1: 1,871'
    Returns: 1871
    """
    if not embed or not embed.footer or not embed.footer.text:
        return None

    footer_text = embed.footer.text
    match = re.search(
        r"wins\s+against\s+NPC\s*\d+\s*:\s*([\d,]+)", footer_text, flags=re.IGNORECASE
    )
    if not match:
        return None

    wins_text = match.group(1).replace(",", "")
    return int(wins_text) if wins_text.isdigit() else None


async def weakness_chart(bot: discord.Client, message: discord.Message):

    embed = message.embeds[0]
    if not embed or not embed.title:
        debug_log(
            f"No embed or title found in message for weakness_chart in {message.channel.name}"
        )
        return
    user_name, enemy_name = extract_name_before_vs(embed.title)
    if user_name in not_weakness_chart_user_names:
        debug_log(
            f"User '{user_name}' is in not_weakness_chart_user_names cache, skipping weakness chart in {message.channel.name}"
        )
        return
    if not user_name or not enemy_name:
        debug_log(
            f"Could not extract user or enemy name from title '{embed.title}' in {message.channel.name}"
        )
        return

    description = (embed.description or "").lower()
    trigger_phrases = [
        f"**{enemy_name}** sent out",
        f"**{enemy_name}** pivoted with",
    ]
    if not any(phrase.lower() in description for phrase in trigger_phrases):
        debug_log(
            f"None of the trigger phrases {trigger_phrases} found in embed description for message in {message.channel.name}, skipping weakness chart"
        )
        return

    from utils.cache.cache_list import mr_weakness_user_cache
    from utils.cache.mr_weakness_cache import load_mr_weakness_user_cache

    different_name = False
    if not mr_weakness_user_cache:  # If cache is empty, load from DB
        await load_mr_weakness_user_cache(bot)
        debug_log(
            f"Weakness chart data not loaded in cache for {message.channel.name}, loaded from DB"
        )

    display_type = get_display_type_via_user_name(user_name)

    debug_log(f"{mr_weakness_user_cache}")
    if display_type is None and user_name not in not_weakness_chart_user_names:
        debug_log(
            f"No display type found in cache for user '{user_name}' in {message.channel.name}"
        )
        # Try to get member object from guild looking up by name, then fetch display type via user ID if found
        member = discord.utils.get(message.guild.members, name=user_name)
        if member:
            different_name = True
            display_type = get_display_type_via_user_id(member.id)
            if display_type is None:
                debug_log(
                    f"No display type found in cache for user ID {member.id} (name '{user_name}') in {message.channel.name}, defaulting to 'off'"
                )
                display_type = "off"
                not_weakness_chart_user_names.add(user_name)
        return
    if display_type.lower() == "off":
        debug_log(
            f"Display type is 'off' for user '{user_name}' in {message.channel.name}, skipping weakness chart"
        )
        not_weakness_chart_user_names.add(user_name)
        return

    # Get footer wins for NPC battles, if present
    npc_wins = extract_npc_wins_from_footer(embed)
    debug_log(f"Extracted npc_wins={npc_wins} from footer in {message.channel.name}")
    if npc_wins is None:
        debug_log(f"No NPC wins found in footer for message in {message.channel.name}")

    # Try to extract enemy Pokemon from embed fields
    enemy_pokemon = extract_enemy_pokemon_from_embed(embed)
    if not enemy_pokemon:
        debug_log(
            f"Could not extract enemy Pokemon from embed fields for message in {message.channel.name}"
        )
        return
    debug_log(
        f"Extracted enemy Pokemon '{enemy_pokemon}' from embed in {message.channel.name}"
    )
    if message.id in processed_weakness_messages:
        debug_log(
            f"Message ID {message.id} already processed for weakness chart in {message.channel.name}, skipping duplicate"
        )
        return
    processed_weakness_messages.add(
        message.id
    )  # Mark this message as processed to avoid duplicates
    try:
        embed_to_send = build_user_weakness_embed_w_o_cache(
            pokemon_input=enemy_pokemon, raw_display_type=display_type
        )
        await _retry_discord_send(lambda: message.channel.send(embed=embed_to_send))
        if different_name and member:
            await update_user_name(bot, member.id, user_name)
            debug_log(
                f"Updated user name in DB for user ID {member.id} to '{user_name}' after extracting from embed title in {message.channel.name}"
            )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Error building/sending weakness embed for user '{user_name}' with enemy '{enemy_pokemon}' in {message.channel.name}: {e}",
            context=EspeonContext.STRAYMONS,
        )
