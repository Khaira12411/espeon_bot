import discord
from config.emojis import PokeCoin
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    update_market_alert,
)
from utils.group_func.market_alert.parsers import resolve_pokemon_input
from utils.loggers.espeon_log import espeon_log
from utils.visuals.embeds.get_log_channel import get_log_channel


async def update_market_alert_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
    max_price: int = None,
    channel: discord.TextChannel | None = None,
    role: discord.Role | None = None,
    notify: bool | None = None,
):
    """
    Update an existing market alert. Sends the embed directly to the interaction.
    Only updates columns for which a new value is provided.
    """
    from utils.cache.market_alert_cache import load_market_alert_cache

    user = interaction.user
    user_id = user.id
    channel_id = channel.id if channel else None
    role_id = role.id if role else None

    if all(v is None for v in [max_price, channel_id, role_id, notify]):
        await interaction.response.send_message(
            "❌ No new values provided for update.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    # ── Resolve Pokémon name & Dex ──
    try:
        pokemon_name, dex_number = resolve_pokemon_input(pokemon)
    except ValueError as e:
        await interaction.followup.send(f"❌ {e}", ephemeral=True)
        return

    # ── Prepare updates dictionary ──
    updates = {}
    if max_price is not None:
        try:
            updates["max_price"] = int(max_price)
        except ValueError:
            await interaction.followup.send(
                "❌ Max price must be an integer.", ephemeral=True
            )
            return
    if channel_id is not None:
        updates["channel_id"] = channel_id
    if role_id is not None:
        updates["role_id"] = role_id
    if notify is not None:
        # Ensure it's a boolean, not a string
        if isinstance(notify, str):
            notify = notify.lower() in ("true", "1", "t", "yes")
        updates["notify"] = notify

    # ── Perform the update ──
    try:
        updated_count = await update_market_alert(
            bot, user_id=user_id, dex_number=dex_number, pokemon=pokemon_name, **updates
        )
        await load_market_alert_cache(bot)
    except Exception as e:
        espeon_log(
            "error",
            f"Failed updating market alert for {user_id}: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.followup.send(
            f"❌ An unexpected error occurred: {e}", ephemeral=True
        )
        return

    # ── Build confirmation embed ──
    fields = []
    if max_price is not None:
        fields.append(("Max Price", f"{PokeCoin} {max_price:,}"))
    if channel_id is not None:
        fields.append(("Channel", f"<#{channel_id}>"))
    if role_id is not None:
        fields.append(("Role", f"<@&{role_id}>"))
    if notify is not None:
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

    await interaction.followup.send(embed=embed, ephemeral=True)
    espeon_log(
        "sent",
        f"Updated {updated_count} alerts for user {user_id} -> {pokemon_name} (Dex #{dex_number})",
        source="MarketAlert",
    )
