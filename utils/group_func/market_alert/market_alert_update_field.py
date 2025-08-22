import discord
from config.emojis import PokeCoin  # your coin emoji
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    update_market_alert,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input


async def update_market_alert_func(
    bot,
    user_id: int,
    pokemon: str,
    max_price: int = None,
    channel_id: int = None,
    role_id: int = None,
    notify: bool = None,
) -> discord.Embed:
    """
    Updates columns for an existing market alert and returns a confirmation embed.
    Only updates columns for which a new value is provided.
    Pokémon itself cannot be changed, but input can be name or Dex.
    """
    from utils.cache.market_alert_cache import load_market_alert_cache

    # ── Validate that at least one column is being updated ──
    if all(v is None for v in [max_price, channel_id, role_id, notify]):
        raise ValueError("No new values provided for update.")

    # ── Resolve Pokémon name and Dex ──
    try:
        pokemon_name, dex_number = resolve_pokemon_input(pokemon)
    except ValueError as e:
        raise ValueError(str(e))

    # ── Prepare updates dictionary ──
    updates = {}
    if max_price is not None:
        try:
            updates["max_price"] = int(max_price)
        except ValueError:
            raise ValueError("Max price must be an integer.")
    if channel_id is not None:
        updates["channel_id"] = channel_id
    if role_id is not None:
        updates["role_id"] = role_id
    if notify is not None:
        updates["notify"] = notify

    # ── Perform the update ──
    updated_count = await update_market_alert(
        bot,
        user_id=user_id,
        dex_number=dex_number,
        pokemon=pokemon_name,
        **updates,
    )
    await load_market_alert_cache(bot)

    # ── Build confirmation embed ──
    fields = []
    if max_price is not None:
        fields.append(("Max Price", f"{PokeCoin} {max_price:,}"))
    if channel_id is not None:
        fields.append(("Channel", f"<#{channel_id}>"))
    if role_id is not None:
        fields.append(("Role", f"<@&{role_id}>"))
    if notify is not None:
        # Show "Enable" / "Disable" instead of True/False
        notify_display = "Enable" if notify else "Disable"
        fields.append(("Notify", notify_display))

    embed = discord.Embed(
        title="💜 Market Alert Updated!",
        description=f"{updated_count} alert(s) successfully updated for {pokemon_name} (Dex #{dex_number})",
        color=0xFF99FF,
    )

    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)

    embed.set_footer(
        text="You'll be notified according to your updated alert settings 💜"
    )
    return embed
