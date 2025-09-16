import discord
from discord import app_commands
from discord.ext import commands

from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from config.wb_constants import *
from utils.database.personal_channel import *
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.group_func.wb_sub.wb_sub_embed import create_wb_embed



# 💜────────────────────────────────────────────
#   🟣 REMOVE WB Subscription
# 💜────────────────────────────────────────────
async def wb_sub_remove_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    boss_name: str,
):
    from utils.group_func.wb_sub.wb_sync import (
        sync_remove_wb_ping,
        sync_remove_all_wb_pings,
    )

    handler = await pretty_defer(
        interaction=interaction,
        content="Processing your WB unsub...",
        ephemeral=False,
    )
    try:
        user = interaction.user
        guild = interaction.guild

        # 🗺️ Remap aliases
        remap = {
            "uss": "uss",
            "urshifu singlestrike": "uss",
            "urs": "urs",
            "urshifu rapidstrike": "urs",
            "ee": "eternatus",
        }

        # ✅ Check if user wants to remove ALL subscriptions
        if boss_name.lower() == "all":
            removed = await sync_remove_all_wb_pings(bot, user.id)

            # 💠 Espeon Log
            espeon_log(
                tag="db",
                message=f"💜 All WB Subs Removed | User: {user.display_name} ({user.id}) | Rows removed: {removed}",
                label="💠 WB SUB",
                context=EspeonContext.STRAYMONS,
            )

            # 📦 User Embed
            embed = discord.Embed(
                title=f"{WBEmojis.WB_Spawn} All WB Pings Removed",
                description=f"{user.mention}, all your WB subscriptions have been removed.",
                color=discord.Color.purple(),
            )
            await handler.success(content="", embed=embed)
            return  # exit early

        # 🗝️ Normal removal: parse selection (boss|variant|mode)
        try:
            boss_name, variant, mode = boss_name.split("|")
        except ValueError:
            await handler.error(
                content="Invalid format. Please provide 'boss|variant|mode' or 'all'."
            )
            return

        lower_boss_name = boss_name.lower()
        key = remap.get(lower_boss_name, lower_boss_name)
        variant = variant.lower()
        mode = mode.lower()

        # Remove from DB/cache
        await sync_remove_wb_ping(bot=bot, user_id=user.id, boss_name=lower_boss_name)

        # 📦 Create User Embed via helper
        embed = create_wb_embed(
            user=user,
            guild=guild,
            boss_name=boss_name,
            variant=variant,
            mode=mode,
            action="removed",
        )
        await handler.success(content="", embed=embed)

        # 📦 Send Log Embed
        log_embed = embed.copy()
        log_embed.set_footer(text=f"User ID: {user.id}", icon_url=guild.icon.url)
        log_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.server_logs)
        if log_channel:
            await log_channel.send(embed=log_embed)

        # 💠 Espeon Log
        espeon_log(
            tag="db",
            message=(
                f"💜 WB Sub Removed | User: {user.display_name} ({user.id}) "
                f"| Boss: {boss_name.title()} | Variant: {variant} | Mode: {mode}"
            ),
            label="💠 WB SUB",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to remove WB Sub for {interaction.user.id}: {e}",
            exc=e,
            label="💠 WB SUB",
            context=EspeonContext.STRAYMONS,
        )
