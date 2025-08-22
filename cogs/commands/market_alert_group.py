# 🟣────────────────────────────────────────────
#           💜 Market Alerts Command Group 💜
# ─────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

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
        try:
            # Validate role
            role_id = None
            if role:
                if role.guild.id != interaction.guild.id:
                    await interaction.response.send_message(
                        "❌ The role you specified is not in this server.",
                        ephemeral=True,
                    )
                    return
                role_id = role.id

            confirmation_embed = await add_market_alert_func(
                bot=self.bot,
                user_id=interaction.user.id,
                pokemon=pokemon,
                max_price=max_price,
                channel_id=channel.id,
                role_id=role_id,
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
        try:
            # Convert notify string to boolean
            notify_bool = None
            if notify is not None:
                notify_bool = notify.lower() == "true"

            # Determine IDs safely
            channel_id = channel.id if channel else None
            role_id = role.id if role else None

            # Call the update function
            embed = await update_market_alert_func(
                bot=self.bot,
                user_id=interaction.user.id,
                pokemon=pokemon,
                max_price=max_price,
                channel_id=channel_id,
                role_id=role_id,
                notify=notify_bool,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: {e}", ephemeral=True
            )

    #
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
        try:
            # ── Handle role removal ──
            role_id: int | None = None
            if isinstance(role, discord.Role):
                role_id = role.id
            elif isinstance(role, str) and role.lower() == "none":
                role_id = None  # user wants to remove the role

            # ── Determine channel ID safely ──
            channel_id = channel.id if channel else None

            # ── Call the update function ──
            embed = await update_market_alert_role_channel_func(
                bot=self.bot,
                user_id=interaction.user.id,
                channel_id=channel_id,
                role_id=role_id,
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
