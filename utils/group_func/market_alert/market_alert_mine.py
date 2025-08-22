import discord

from config.emojis import PokeCoin  # your coin emoji
from utils.group_func.market_alert.db_func.market_alert_db_func import fetch_user_alerts


# 🟪────────────────────────────────────────────
#   Mine Market Alerts
# 🟪────────────────────────────────────────────
async def mine_market_alerts_func(bot, user_id: int) -> discord.Embed:
    """
    Fetch and display all market alerts owned by a user in a cute styled embed.
    """
    alerts = await fetch_user_alerts(bot, user_id)

    if not alerts:
        return discord.Embed(
            title="💜 No Market Alerts",
            description="You don’t have any active market alerts right now.\n"
            "Use `/market-alert add` to create one ✨",
            color=0xAA88FF,
        )

    embed = discord.Embed(
        title="💜 Your Market Alerts",
        description="Here’s a list of your current market alerts:\n",
        color=0xAA88FF,
    )

    for alert in alerts:
        role_mention = f"<@&{alert['role_id']}>" if alert.get("role_id") else "None"
        notify_status = "✅ Enabled" if alert.get("notify", True) else "❌ Disabled"

        embed.add_field(
            name=f"✨ {alert['pokemon'].title()} (Dex #{alert['dex_number']})",
            value=(
                f"> - **Max Price:** {PokeCoin} {alert['max_price']:,}\n"
                f"> - **Channel:** <#{alert['channel_id']}>\n"
                f"> - **Role:** {role_mention}\n"
                f"> - **Notify:** {notify_status}"
            ),
            inline=False,
        )

    embed.set_footer(
        text="💜 Use /market-alert remove or /market-alert toggle to manage these alerts!"
    )

    return embed
import discord
from config.emojis import PokeCoin
from utils.group_func.market_alert.db_func.market_alert_db_func import fetch_user_alerts


# 🟪────────────────────────────────────────────
#   Mine Market Alerts (with pagination + page numbers)
# 🟪────────────────────────────────────────────
async def build_market_alert_embeds(bot, user_id: int) -> list[discord.Embed]:
    """
    Build paginated embeds for a user's market alerts.
    Auto-splits if >25 fields or ~5500 chars.
    Adds Page X/Y footer.
    """
    alerts = await fetch_user_alerts(bot, user_id)

    if not alerts:
        return [
            discord.Embed(
                title="💜 No Market Alerts",
                description="You don’t have any active market alerts right now.\n"
                "Use `/market-alert add` to create one ✨",
                color=0xAA88FF,
            )
        ]

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

        # check embed limits
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

    # add footer with pagination info
    total_pages = len(embeds)
    for i, e in enumerate(embeds, start=1):
        e.set_footer(
            text=f"💜 Use /market-alert remove or /market-alert toggle to manage these alerts! | Page {i}/{total_pages}"
        )

    return embeds

import discord


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
