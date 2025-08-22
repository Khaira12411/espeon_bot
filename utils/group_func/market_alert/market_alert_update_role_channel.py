import discord

from config.emojis import PokeCoin  # your coin emoji
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    update_user_alerts_channel_or_role,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input


async def update_market_alert_role_channel_func(
    bot,
    user_id: int,
    channel_id: int = None,
    role_id: int | None = None,  # role_id can now be None explicitly for removal
) -> discord.Embed:
    """
    Updates a user's market alerts with new channel and/or role.
    Only updates fields that are provided.
    Supports removing the role by passing None.
    Returns a confirmation embed.
    """
    if channel_id is None and role_id is None:
        raise ValueError("You must provide at least a new channel or role to update.")

    from utils.cache.market_alert_cache import load_market_alert_cache

    # ── Update database ──
    updated_count = await update_user_alerts_channel_or_role(
        bot, user_id=user_id, channel_id=channel_id, role_id=role_id
    )
    await load_market_alert_cache(bot)

    # ── Build confirmation embed ──
    description_parts = []

    if channel_id is not None:
        description_parts.append(f"Channel updated to <#{channel_id}>")

    if role_id is not None:
        description_parts.append(f"Role updated to <@&{role_id}>")
    else:
        description_parts.append("Role removed")

    description_text = "\n".join(description_parts)

    embed = discord.Embed(
        title="💜 Market Alert Updated!",
        description=f"{updated_count} alert(s) successfully updated!\n{description_text}",
        color=0xFF99FF,
    )

    embed.set_footer(
        text="You'll be notified according to your updated alert settings 💜"
    )
    return embed
