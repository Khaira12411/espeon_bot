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
#   🟣 UPDATE WB Subscription
# 💜────────────────────────────────────────────
async def wb_sub_update_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    boss_name: str,  # comes from autocomplete (boss|variant|mode)
    new_variant: str,
    new_mode: str,
):
    from utils.group_func.wb_sub.wb_sync import sync_update_variant_mode

    handler = await pretty_defer(
        interaction=interaction,
        content="Updating your WB subscription...",
        ephemeral=False,
    )
    try:
        user = interaction.user
        guild = interaction.guild

        # Parse selection (boss|variant|mode)
        boss_name, old_variant, old_mode = boss_name.split("|")
        boss_name = boss_name.lower()

        # Normalize inputs
        new_variant = new_variant.lower()
        new_mode = new_mode.lower()

        # 🔹 Update DB without overwriting channel_id
        updated = await sync_update_variant_mode(
            bot=bot,
            user_id=user.id,
            boss_name=boss_name,
            new_variant=new_variant,
            new_mode=new_mode,
        )

        if not updated:
            await handler.fail(
                content=f"Could not update your subscription for **{boss_name.title()}**."
            )
            return

        # 📦 Create User Embed using helper
        # We'll add old→new info in the description
        embed = create_wb_embed(
            user=user,
            guild=guild,
            boss_name=boss_name,
            variant=new_variant,
            mode=new_mode,
            action="updated",
        )
        # Append old variant/mode info to description
        embed.description += f"\n\n**Old:** {old_variant} / {old_mode}"

        await handler.success(content="", embed=embed)

        # 📦 Create Log Embed
        log_embed = embed.copy()
        log_embed.set_footer(text=f"User ID: {user.id}", icon_url=guild.icon.url)
        log_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.server_logs)
        if log_channel:
            await log_channel.send(embed=log_embed)

        # 📝 Espeon Log
        espeon_log(
            tag="db",
            message=(
                f"🔄 WB Sub Updated | User: {user.display_name} ({user.id}) | "
                f"Boss: {boss_name} | {old_variant}/{old_mode} → {new_variant}/{new_mode}"
            ),
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to update WB Sub for {interaction.user.id}: {e}",
            context=EspeonContext.STRAYMONS,
            exc=e,
        )
