# 🟪────────────────────────────────────────────
#   Mine Market Alerts Brain 💜
# 🟪────────────────────────────────────────────

import discord

from config.emojis import PokeCoin
from utils.group_func.market_alert.db_func.market_alert_db_func import fetch_user_alerts
from utils.loggers.espeon_log import espeon_log


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


async def mine_market_alerts_func(bot, interaction: discord.Interaction):
    """
    Fetch all market alerts for a user, build embeds with pagination if needed,
    and send them directly to the interaction.
    """
    user = interaction.user
    user_id = interaction.user.id
    await interaction.response.defer(ephemeral=True)

    try:
        alerts = await fetch_user_alerts(bot, user_id)
        if not alerts:
            embed = discord.Embed(
                title="💜 No Market Alerts",
                description="You don’t have any active market alerts right now.\n"
                "Use `/market-alert add` to create one ✨",
                color=0xAA88FF,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Build embeds
        embeds = []
        embed = discord.Embed(
            title="💜 Your Market Alerts",
            description="Here’s a list of your current market alerts:\n",
            color=0xAA88FF,
        )
        char_count = len(embed.description)

        for alert in alerts:
            field_name = f"✨ {alert['pokemon'].title()} (Dex #{alert['dex_number']})"
            role_mention = f"<@&{alert['role_id']}>" if alert.get("role_id") else "None"
            notify_status = "✅ Enabled" if alert.get("notify", True) else "❌ Disabled"
            field_value = (
                f"> - **Max Price:** {PokeCoin} {alert['max_price']:,}\n"
                f"> - **Channel:** <#{alert['channel_id']}>\n"
                f"> - **Role:** {role_mention}\n"
                f"> - **Notify:** {notify_status}"
            )

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

        total_pages = len(embeds)
        for i, e in enumerate(embeds, start=1):
            e.set_footer(
                text=f"💜 Use /market-alert remove or /market-alert toggle to manage these alerts! | Page {i}/{total_pages}"
            )

        # Send paginated or single
        if len(embeds) == 1:
            await interaction.followup.send(embed=embeds[0], ephemeral=True)
        else:
            view = MarketAlertPaginator(embeds)
            await interaction.followup.send(embed=embeds[0], view=view, ephemeral=True)

        espeon_log(
            "sent",
            f"Sent market alerts to user {user_id} ({len(alerts)} alerts)",
            source="MarketAlert",
        )

    except Exception as e:
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
