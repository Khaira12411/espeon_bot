# 🟣────────────────────────────────────────────
#           💜 Market Alerts Command Group 💜
# ─────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_safe import run_command_safe
from utils.group_func.market_alert import *


# 🟣────────────────────────────────────────────
#           💜 MarketAlerts Cog Setup 💜
# ─────────────────────────────────────────────
class MarketAlerts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #           💜 Slash Command Group 💜
    # 🟣────────────────────────────────────────────
    market_alerts_group = app_commands.Group(
        name="market-alert", description="Commands related to market alerts"
    )

    # 🟣────────────────────────────────────────────
    #           💜 /market-alert add 💜
    # 🟣────────────────────────────────────────────
    @market_alerts_group.command(name="add", description="Set a new market alert")
    @app_commands.describe(
        pokemon="Pokémon name or Dex number",
        max_price="Maximum price in PokeCoin",
        channel="Channel to send alerts",
        role="Optional role to ping",
    )
    async def add_alert(
        self,
        interaction: discord.Interaction,
        pokemon: str,
        max_price: int,
        channel: discord.TextChannel,
        role: discord.Role | None = None,
    ):

        slash_cmd_name = "market-alert add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=add_market_alert_func,
            pokemon=pokemon,
            max_price=max_price,
            channel=channel,
            role=role,
        )

    add_alert.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /market-alert remove 💜
    # 🟣────────────────────────────────────────────
    @market_alerts_group.command(
        name="remove",
        description="Remove a market alert for a Pokémon, Dex number, or all",
    )
    @app_commands.describe(
        pokemon="Pokémon name, Dex number, or 'all' to remove all alerts"
    )
    async def remove_alert(self, interaction: discord.Interaction, pokemon: str):

        slash_cmd_name = "market-alert remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=remove_market_alert_func,
            pokemon=pokemon,
        )

    remove_alert.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /market-alert mine 💜
    # 🟣────────────────────────────────────────────
    @market_alerts_group.command(
        name="mine", description="View all your active market alerts"
    )
    async def mine_alerts(self, interaction: discord.Interaction):

        slash_cmd_name = "market-alert mine"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=mine_market_alerts_func,
        )

    mine_alerts.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /market-alert toggle 💜
    # 🟣────────────────────────────────────────────
    @market_alerts_group.command(
        name="toggle",
        description="Toggle whether a market alert notifies you (on/off)",
    )
    @app_commands.describe(
        pokemon="Pokémon name, Dex number, or 'all' to toggle all alerts",
        value="true = enable notifications, false = disable notifications",
    )
    async def toggle_alert(
        self, interaction: discord.Interaction, pokemon: str, value: bool
    ):

        slash_cmd_name = "market-alert toggle"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=toggle_market_alert_func,
            pokemon=pokemon,
            value=value,
        )

    toggle_alert.extras = {"category": "Public"}
    #
    # 🟣────────────────────────────────────────────
    #           💜 /market-alert update 💜
    # 🟣────────────────────────────────────────────

    @market_alerts_group.command(
        name="update",
        description="Updates a market alert for a Pokémon",
    )
    @app_commands.describe(
        pokemon="Pokémon name or Dex number",
        max_price="Maximum price in PokeCoin",
        channel="Channel to send alerts",
        role="Role to ping",
        notify="Enable or disable notifications",
    )
    @app_commands.choices(
        notify=[
            app_commands.Choice(name="Enable", value="true"),
            app_commands.Choice(name="Disable", value="false"),
        ]
    )
    async def update_market_alert(
        self,
        interaction: discord.Interaction,
        pokemon: str,
        max_price: int | None = None,
        channel: discord.TextChannel | None = None,
        role: discord.Role | None = None,
        notify: str | None = None,  # Choice strings
    ):
        slash_cmd_name = "market-alert update"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=update_market_alert_func,
            pokemon=pokemon,
            max_price=max_price,
            channel=channel,
            role=role,
            notify=notify,
        )

    update_market_alert.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /market-alert bulk-update 💜
    # 🟣────────────────────────────────────────────

    @market_alerts_group.command(
        name="bulk-update",
        description="Change the channel or role for all of your existing market alerts at once",
    )
    @app_commands.describe(
        channel="Channel to send alerts",
        role="Role to ping (type 'none' to remove the role)",
    )
    async def update_market_alert_bulk(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
        role: discord.Role | None = None,  # ✅ correct
    ):
        slash_cmd_name = "market-alert update"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=update_market_alert_role_channel_func,
            channel=channel,
            role=role,
        )

    update_market_alert_bulk.extras = {"category": "Public"}
    # 🟣────────────────────────────────────────────
    #           💜 /market-alert register 💜
    # 🟣────────────────────────────────────────────
    @market_alerts_group.command(
        name="register", description="Registers you for market alerts based on roles"
    )
    async def market_alert_register(self, interaction: discord.Interaction):

        slash_cmd_name = "market-alert register"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=market_alert_register_func,
        )

    market_alert_register.extras = {"category": "Public"}

# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MarketAlerts(bot))
