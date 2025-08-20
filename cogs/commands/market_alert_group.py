# 🟣────────────────────────────────────────────
#           💜 Market Alerts Command Group 💜
# ─────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from utils.group_func.market_alert.market_alert_add import add_market_alert_func
from utils.group_func.market_alert.market_alert_remove import remove_market_alert_func
from utils.group_func.market_alert.market_alert_mine import mine_market_alerts_func
from utils.group_func.market_alert.market_alert_toggle import toggle_market_alert_func


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
        role: discord.Role = None,
    ):
        try:
            confirmation_embed = await add_market_alert_func(
                bot=self.bot,
                user_id=interaction.user.id,
                pokemon=pokemon,
                max_price=max_price,
                channel_id=channel.id,
                role_id=role.id if role else None,
            )
            await interaction.response.send_message(
                embed=confirmation_embed, ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Failed to add market alert: {e}", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: {e}", ephemeral=True
            )

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
        try:
            embed = await remove_market_alert_func(
                bot=self.bot, user_id=interaction.user.id, pokemon=pokemon
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: {e}", ephemeral=True
            )

    # 🟣────────────────────────────────────────────
    #           💜 /market-alert mine 💜
    # 🟣────────────────────────────────────────────
    @market_alerts_group.command(
        name="mine", description="View all your active market alerts"
    )
    async def mine_alerts(self, interaction: discord.Interaction):
        try:
            embed = await mine_market_alerts_func(
                bot=self.bot, user_id=interaction.user.id
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ An unexpected error occurred while fetching alerts: {e}",
                ephemeral=True,
            )

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
        try:
            embed = await toggle_market_alert_func(
                bot=self.bot, user_id=interaction.user.id, pokemon=pokemon, value=value
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: {e}", ephemeral=True
            )


# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MarketAlerts(bot))
