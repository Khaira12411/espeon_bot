import time

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import *
from config.current_setup import KHY_USER_ID
from utils.essentials.loader import pretty_defer
from utils.group_func.afk.afk_db_func import *
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc


# 🤍────────────────────────────────────────────
#   AFK Set Function (Slash Command Helper)
# 🤍────────────────────────────────────────────
async def afk_set_func(
    bot: commands.Bot, interaction: discord.Interaction, reason: str
):
    handler = await pretty_defer(
        interaction=interaction,
        content="Setting up your AFK Status...",
        ephemeral=False,
    )
    user = interaction.user
    started_at = int(time.time())
    nickname_status = "⚠️ Nickname unchanged"

    try:
        # 📌 Upsert AFK in DB + Cache
        await upsert_afk(
            bot=bot,
            user_id=user.id,
            user_name=str(user),
            reason=reason,
            started_at=started_at,
        )

        # 🟣 Try adding [AFK] to nickname (if possible)
        if isinstance(user, discord.Member):  # only in guild context
            if user.id == KHY_USER_ID:
                espeon_log(
                    tag="info",
                    message=f"[🤍 AFK] Skipping nickname edit for {user.display_name} (server owner)",
                    context=EspeonContext.STRAYMONS,
                )
                nickname_status = "👑 Nickname skipped (Server Owner)"
            else:
                current_nick = user.nick or user.name
                if not current_nick.startswith("[AFK]"):
                    new_nick = f"[AFK] {current_nick}"
                    try:
                        await user.edit(nick=new_nick, reason="User set AFK")
                        nickname_status = "✏️ Nickname updated"
                    except discord.Forbidden:
                        espeon_log(
                            tag="warn",
                            message=f"[🤍 AFK] Missing perms to edit nickname for {user.display_name}",
                            context=EspeonContext.STRAYMONS,
                        )
                        nickname_status = "⚠️ Nickname unchanged (missing perms)"
                    except Exception as e:
                        espeon_log(
                            tag="error",
                            message=f"[💜 AFK] Failed to edit nickname for {user.display_name}: {e}",
                            context=EspeonContext.STRAYMONS,
                        )
                        nickname_status = "⚠️ Nickname unchanged (error)"

        # ✨ Build confirmation embed
        embed = discord.Embed(
            title="🌙 AFK Status Set",
            description=(
                f"👤 **User:** {user.mention}\n"
                f"💭 **Reason:** {reason or '*No reason provided*'}\n"
                f"⏱️ **Since:** <t:{started_at}:R>\n"
                f"{nickname_status}"
            ),
        )

        footer_text = "🦋 AFK mode enabled — stay cozy!"
        embed = design_embed(
            embed=embed,
            user=user,
            footer_text=footer_text,
            thumbnail_url=Espeon_Thumbnail.afk_set,
        )

        await handler.success(content="", embed=embed)
        espeon_log(
            tag="afk",
            message=f"[💙 AFK] {user.display_name} set AFK → {reason}",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        # ❌ On error, log + inform user
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to set AFK for {user.display_name}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        await handler.error(
            content="Sorry, something went wrong while setting your AFK."
        )
