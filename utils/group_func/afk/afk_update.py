
# 🤍────────────────────────────────────────────
#   AFK Update Function (Slash Command Helper)
# 🤍────────────────────────────────────────────
import time

import discord
from discord.ext import commands

from config.aesthetic import *
from utils.essentials.loader import pretty_defer
from utils.group_func.afk.afk_db_func import *
from utils.visuals.embeds.visual_helpers import design_embed


async def afk_update_func(
    bot: commands.Bot, interaction: discord.Interaction, reason: str
):
    user = interaction.user
    updated_at = int(time.time())

    handler = await pretty_defer(
        interaction=interaction,
        content="Updating your AFK Status...",
        ephemeral=False,
    )
    try:
        # 📌 Check if user already has AFK row
        from utils.cache.afk_user_cache import AFK_CACHE

        afk_row = AFK_CACHE.get(user.id)
        if not afk_row:
            await handler.error(
                content="❌ You’re not marked as AFK yet. Use `/afk-set` first!"
            )
            return

        # 📌 Update AFK status in DB + Cache
        await update_afk_reason(
            bot=bot, user_id=user.id, user_name=user.name, reason=reason
        )

        # ✨ Build confirmation embed
        embed = discord.Embed(
            title="🌙 AFK Status Updated",
            description=(
                f"👤 **User:** {user.mention}\n"
                f"💭 **New Reason:** {reason or '*No reason provided*'}\n"
                f"⏱️ **Updated at:** <t:{updated_at}:R>"
            ),
        )
        footer_text = "🌸 New AFK note saved — soft & simple"
        embed = await design_embed(
            embed=embed,
            user=user,
            footer_text=footer_text,
            thumbnail_url=Espeon_Thumbnail.afk_update,
        )

        await handler.success(content="", embed=embed)
        espeon_log(
            tag="afk",
            message=f"[💙 AFK] Updated AFK reason for {user.display_name} → {reason}",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        # ❌ On error, log + inform user
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to update AFK for {user.display_name}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await handler.error(
            content="Sorry, something went wrong while updating your AFK."
        )
