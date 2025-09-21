import time

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import *
from utils.essentials.loader import pretty_defer
from utils.group_func.afk.afk_db_func import *
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc


# 🤍────────────────────────────────────────────
#   AFK Remove Function (Slash Command Helper)
# 🤍────────────────────────────────────────────
async def afk_remove_func(bot: commands.Bot, interaction: discord.Interaction):
    user = interaction.user

    handler = await pretty_defer(
        interaction=interaction,
        content="Removing your AFK Status...",
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

        # 📌 Clear row in DB
        await clear_afk(bot=bot, user_id=user.id, user_name=user.name)

        # 📝 Remove [AFK] from nickname if present
        try:
            if isinstance(user, discord.Member):
                current_nick = user.nick or user.name
                if current_nick.startswith("[AFK] "):
                    new_nick = current_nick[len("[AFK] ") :]
                    await user.edit(nick=new_nick, reason="AFK status removed")
        except discord.Forbidden:
            espeon_log(
                tag="warn",
                message=f"[AFK] Could not remove nickname prefix for {user} (missing perms).",
                context=EspeonContext.STRAYMONS,
            )
        except Exception as e:
            espeon_log(
                tag="error",
                message=f"[AFK] Failed to update nickname for {user}: {e}",
                context=EspeonContext.STRAYMONS,
            )

        # ✨ Send Success message
        await handler.success(content="Successfully removed your AFK status")
        espeon_log(
            tag="afk",
            message=f"[💙 AFK] {user.display_name} removed their AFK Status",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        # ❌ On error, log + inform user
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to remove AFK for {user.display_name}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await handler.error(
            content="Sorry, something went wrong while removing your AFK."
        )
