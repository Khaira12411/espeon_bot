# 🟪────────────────────────────────────────────
#   Mine Market Alerts Brain 💜
# 🟪────────────────────────────────────────────

import discord

from config.aesthetic import *
from config.emojis import PokeCoin
from utils.essentials.loader import pretty_defer
from utils.group_func.market_alert.db_func.market_alert_counter import (
    get_market_alert_status,
)
from utils.group_func.market_alert.db_func.market_alert_db_func import fetch_user_alerts
from utils.loggers.espeon_log import espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc


# 🍇──────────────────────────────
#      🌀 Market Alert Paginator
# 🍇──────────────────────────────
class MarketAlertPaginator(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.index = 0

    @discord.ui.button(label="⬅️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.index = (self.index - 1) % len(self.embeds)
        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.index = (self.index + 1) % len(self.embeds)
        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )


# 🌸──────────────────────────────
#       💜 Mine Market Alerts
# 🌸──────────────────────────────
async def mine_market_alerts_func(bot, interaction: discord.Interaction):
    """
    Fetch all market alerts for a user, build embeds with pagination if needed,
    and send them directly to the interaction.
    """
    user = interaction.user
    user_id = user.id

    # ⏳ Pretty loader while fetching
    handle = await pretty_defer(
        interaction=interaction, content="Fetching your Market Alerts..."
    )

    # 📊 Get user status
    status = await get_market_alert_status(bot=bot, user=user)
    status_message = status["message"]

    try:
        alerts = await fetch_user_alerts(bot, user_id)

        # 🟣 No alerts case
        if not alerts:
            embed = discord.Embed(
                title=f"{Espeon_Emoji.purple_flower} No Market Alerts",
                description="You don’t have any active market alerts right now.",
                color=0xAA88FF,
            )
            embed = await design_embed(
                embed=embed,
                user=user,
                footer_text="Use /market-alert add` to create one ✨",
                thumbnail_url=Espeon_Thumbnail.purple_list,
            )
            await handle.stop(embed=embed)
            return

        # 🟣 Build alert embeds
        embeds = []
        embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_flower} Your Market Alerts",
            description=f"{status_message}\n{Espeon_Emoji.purple_message} Here’s a list of your current market alerts:\n\n",
            color=0xAA88FF,
        )
        embed.set_thumbnail(url=Espeon_Thumbnail.purple_list)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        char_count = len(embed.description)

        for alert in alerts:
            field_name = f"{Espeon_Emoji.purple_plushie} {alert['pokemon'].title()} (Dex #{alert['dex_number']})"
            role_mention = f"<@&{alert['role_id']}>" if alert.get("role_id") else "None"
            notify_status = "✅ Enabled" if alert.get("notify", True) else "❌ Disabled"
            field_value = (
                f"> - **Max Price:** {PokeCoin} {alert['max_price']:,}\n"
                f"> - **Channel:** <#{alert['channel_id']}>\n"
                f"> - **Role:** {role_mention}\n"
                f"> - **Notify:** {notify_status}"
            )

            # Split embeds if field/char limits exceeded
            if (
                len(embed.fields) >= 25
                or (char_count + len(field_name) + len(field_value)) > 5500
            ):
                embeds.append(embed)
                embed = discord.Embed(
                    title="💜 Your Market Alerts (continued)",
                    color=0xAA88FF,
                )
                char_count = 0

            embed.add_field(name=field_name, value=field_value, inline=False)
            char_count += len(field_name) + len(field_value)

        embeds.append(embed)

        # Footer & pagination info
        total_pages = len(embeds)
        for i, e in enumerate(embeds, start=1):
            e.set_footer(
                text=f"💜 Use /market-alert remove or /market-alert toggle to manage these alerts! | Page {i}/{total_pages}"
            )

        # 🟢 Send single or paginated embed
        if len(embeds) == 1:
            await handle.stop(embed=embeds[0])
        else:
            view = MarketAlertPaginator(embeds)
            await handle.stop(embed=embeds[0], view=view)

        # 📦 Log success
        espeon_log(
            "sent",
            f"Sent market alerts to user {user_id} ({len(alerts)} alerts)",
            source="MarketAlert",
        )

    except Exception as e:
        # ❌ Error handling
        espeon_log(
            "error",
            f"Failed to fetch or send market alerts: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.followup.send(
            f"❌ Failed to fetch market alerts: {e}", ephemeral=True
        )
