import discord
from config.emojis import PokeCoin
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    update_user_alerts_channel_or_role,
)
from utils.loggers.espeon_log import espeon_log


async def update_market_alert_role_channel_func(
    bot,
    interaction: discord.Interaction,
    channel: discord.TextChannel | None = None,
    role: discord.Role | str | None = None,
):
    """
    Updates all of a user's market alerts with a new channel and/or role.
    Sends the embed directly to the interaction.
    Supports removing the role by passing 'none' or None.
    """
    user = interaction.user
    user_id = user.id
    await interaction.response.defer(ephemeral=True)

    # ── Determine role ID ──
    role_id: int | None = None
    if isinstance(role, discord.Role):
        role_id = role.id
    elif isinstance(role, str) and role.lower() == "none":
        role_id = None  # user wants to remove the role

    # ── Determine channel ID ──
    channel_id = channel.id if channel else None

    if channel_id is None and role_id is None:
        await interaction.followup.send(
            "❌ You must provide at least a new channel or role to update.",
            ephemeral=True,
        )
        return

    # ── Update database ──
    try:
        updated_count = await update_user_alerts_channel_or_role(
            bot, user_id=user_id, channel_id=channel_id, role_id=role_id
        )
        from utils.cache.market_alert_cache import load_market_alert_cache

        await load_market_alert_cache(bot)
    except Exception as e:
        espeon_log(
            "error",
            f"Failed bulk updating alerts for {user_id}: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.followup.send(
            f"❌ An unexpected error occurred: {e}", ephemeral=True
        )
        return

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
        title="💜 Market Alerts Bulk Updated!",
        description=f"{updated_count} alert(s) successfully updated!\n{description_text}",
        color=0xFF99FF,
    )
    embed.set_footer(
        text="You'll be notified according to your updated alert settings 💜"
    )

    await interaction.followup.send(embed=embed, ephemeral=True)
    espeon_log(
        "sent",
        f"Bulk updated {updated_count} alerts for user {user_id}",
        source="MarketAlert",
    )
