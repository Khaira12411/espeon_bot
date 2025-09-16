import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import *
from config.wb_constants import WBEmojis
from utils.essentials.loader import pretty_defer


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › WB VIEW ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━
async def wb_view_func(bot: commands.Bot, interaction: discord.Interaction):
    """
    Returns an embed showing all WB subscriptions for a user.
    Fetches from cache, reloads if missing.
    """
    user = interaction.user
    guild = interaction.guild

    from utils.cache.wb_sub_cache import WB_PING_CACHE, load_wb_ping_cache

    handler = await pretty_defer(
        interaction=interaction, content="Fetching your WB pings...", ephemeral=False
    )
    user_id = user.id
    data = WB_PING_CACHE.get(user_id)
    if not data:
        await load_wb_ping_cache(bot)
        data = WB_PING_CACHE.get(user_id)

    user_wb_data = data or {}
    thumbnail_url = Espeon_Thumbnail.boss
    if not user_wb_data:
        embed = discord.Embed(
            title=f"{WBEmojis.WB_Spawn} Your WB Pings",
            description=f"❌ {user.mention}, you have no world boss subscriptions set.",
            color=0xFF99FF,
        )
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)
        handler.stop(embed=embed)
        return

    # Build description
    desc_lines = []

    for boss_name, info in user_wb_data.items():
        mode = info.get("mode", "Off").title()
        variant = info.get("variant", "regular").lower()  # <-- use lowercase for logic
        channel_id = info.get("channel_id")
        created_at = info.get("created_at")

        # 📝 Determine variant display
        if variant == "regular":
            display_variant = f"{WBEmojis.Gmax} Regular"
        elif variant == "shiny":
            display_variant = f"{WBEmojis.Sgmax} Shiny"
        elif variant == "both":
            display_variant = f"{WBEmojis.Gmax} Regular, and {WBEmojis.Sgmax} Shiny"
        else:
            display_variant = variant.title()

        channel_display = f"<#{channel_id}>" if channel_id else "Unknown channel"
        timestamp_display = (
            f"<t:{int(created_at.timestamp())}:f>" if created_at else "Unknown time"
        )

        desc_lines.append(
            f"{WBEmojis.WB_Spawn} **{boss_name.title()}**\n"
            f"**Variant** → {display_variant}\n"
            f"**Mode** → {mode}\n"
            f"**Channel** → {channel_display}\n"
            f"**Created At** → {timestamp_display}"
        )

    embed = discord.Embed(
        title=f"{WBEmojis.WB_Spawn} Your WB Pings",
        description="\n\n".join(desc_lines),
        color=0xFF99FF,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(
        text=f"Check your WB subscriptions anytime | Total: {len(user_wb_data)} ✨",
        icon_url=guild.icon.url,
    )
    await handler.success(content="", embed=embed)
