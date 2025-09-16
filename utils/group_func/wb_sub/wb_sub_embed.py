# 💜────────────────────────────────────────────
#   🟣 WB Embed Creator
# 💜────────────────────────────────────────────
import discord

from config.wb_constants import WBColors, WBEmojis, WBRegImage, WBShinyImage
from utils.visuals.embeds.visual_helpers import format_bulletin_desc


def create_wb_embed(
    user: discord.User | discord.Member,
    guild: discord.Guild,
    boss_name: str,
    variant: str,
    mode: str,
    action: str = "added",  # "added", "updated", "removed"
) -> discord.Embed:
    """
    Returns a fully formatted WB embed.
    """
    # 🗺️ Remap aliases
    remap = {
        "uss": "uss",
        "urshifu-singlestrike": "uss",
        "urs": "urs",
        "urshifu-rapidstrike": "urs",
        "ee": "eternatus",
    }
    lower_boss_name = boss_name.lower()
    key = remap.get(lower_boss_name, lower_boss_name)
    variant = variant.lower()
    upper_boss = boss_name.upper()

    # 🧠 Determine boss display name, color, image
    if key == "eternatus":
        display_name = "ETERNAMAX-ETERNATUS"
        if variant in ("regular", "both"):
            color = WBColors.eternatus
            image = WBRegImage.eternatus
        else:
            display_name = "SHINY ETERNAMAX-ETERNATUS"
            color = WBColors.Shiny
            image = WBShinyImage.eternatus
    else:
        display_name = (
            "URSHIFU-SINGLESTRIKE"
            if key == "uss"
            else (
                "URSHIFU-RAPIDSTRIKE"
                if key == "urs"
                else (
                    f"SHINY GIGANTAMAX-{upper_boss}"
                    if variant in ("shiny", "both")
                    else f"GIGANTAMAX-{upper_boss}"
                )
            )
        )
        color = (
            WBColors.Shiny
            if variant in ("shiny", "both")
            else getattr(WBColors, key, discord.Color.greyple())
        )
        image = getattr(
            WBShinyImage if variant in ("shiny", "both") else WBRegImage,
            key,
            None,
        )

    # 📝 Determine variant display
    if variant == "regular":
        display_variant = f"{WBEmojis.Gmax} Regular"
    elif variant == "shiny":
        display_variant = f"{WBEmojis.Sgmax} Shiny"
    elif variant == "both":
        display_variant = f"{WBEmojis.Gmax} Regular, and {WBEmojis.Sgmax} Shiny"
    else:
        display_variant = variant.title()

    # 📦 Description
    desc = format_bulletin_desc(
        "Member",
        user.mention,
        "Boss",
        display_name.replace("SHINY ", "").title(),
        "Variant",
        display_variant,
        "Mode",
        mode.title(),
    )

    # 📦 Build embed
    embed = discord.Embed(
        title=f"{WBEmojis.WB_Spawn} WB Ping {action.title()}",
        description=desc,
        color=color,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar)

    if image:
        embed.set_thumbnail(url=image)
    embed.set_footer(
        text="Check your WB subscriptions with /settings",
        icon_url=guild.icon.url,
    )

    return embed
