# 💠───────────────────────────────────────────────────────────────
# [📦 IMPORTS] Discord, Configs, and Utilities
# ────────────────────────────────────────────────────────────────
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import *
from config.current_setup import KHY_USER_ID
from utils.essentials.role_checks import *
from utils.loggers.espeon_log import espeon_log

# 🏷 Replace with your guild ID
OWNER_ID = KHY_USER_ID  # 👑 your Discord user ID
EMBED_COLOR = 9323693
DEFAULT_THUMBNAIL = Espeon_Thumbnail.espeon_sun
DEFAULT_IMAGE_URL = Esepon_Divider.purple_flowers
# 💠───────────────────────────────────────────────────────────────
# [⚙️ CONFIG] Category Settings
# ────────────────────────────────────────────────────────────────
CATEGORY_CONFIG = {
    "Public": {
        "emoji": Espeon_Emoji.sun,
        "label": "Public",
        "color": discord.Color(15117266),
        "thumbnail": Espeon_Thumbnail.sunflower,
    },
    "Owner": {
        "emoji": Espeon_Emoji.moon,
        "label": "Owner",
        "color": discord.Color(7091331),
        "thumbnail": Espeon_Thumbnail.purple_witch_cat,
    },
}


# 💠───────────────────────────────────────────────────────────────
# [🧩 HELPER] Flatten commands and include group prefixes
# ────────────────────────────────────────────────────────────────
def flatten_commands(commands_list, parent_name="") -> list[app_commands.Command]:
    flattened = []
    for cmd in commands_list:
        if isinstance(cmd, app_commands.Group):
            new_parent = f"{parent_name} {cmd.name}".strip()
            flattened.extend(flatten_commands(cmd.commands, new_parent))
        else:
            cmd.full_name = (
                f"/{parent_name} {cmd.name}".strip() if parent_name else f"/{cmd.name}"
            )
            flattened.append(cmd)
    return flattened


# 💠───────────────────────────────────────────────────────────────
# [📄 VIEW] Paginated View
# ────────────────────────────────────────────────────────────────
class PaginatedCategoryView(discord.ui.View):
    def __init__(self, user, category, commands_list, command_map):
        super().__init__(timeout=120)
        self.user = user
        self.category = category
        self.commands = commands_list
        self.page = 0
        self.per_page = 6
        self.max_page = (len(self.commands) - 1) // self.per_page
        self.command_map = command_map
        self.message: discord.Message = None
        self.add_navigation_buttons()

    def add_navigation_buttons(self):
        self.clear_items()
        if self.page > 0:
            self.add_item(PageNavButton("⬅️", self, -1))
        if self.page < self.max_page:
            self.add_item(PageNavButton("➡️", self, 1))
        # ✅ Always show home button
        self.add_item(BackHomeButton(self.user, self.command_map))

    async def send_page(self):
        try:
            cfg = CATEGORY_CONFIG[self.category]
            start = self.page * self.per_page
            end = start + self.per_page
            cmds = self.commands[start:end]

            embed = discord.Embed(
                title=f"{cfg['emoji']} {cfg['label']} Commands",
                color=cfg["color"],
            )
            embed.set_author(
                name=self.user.display_name, icon_url=self.user.display_avatar.url
            )
            if cfg.get("thumbnail"):
                embed.set_thumbnail(url=cfg["thumbnail"])

            for cmd in cmds:
                command_name = getattr(cmd, "full_name", "/" + cmd.name)
                embed.add_field(
                    name=command_name,
                    value=cmd.description or "No description",
                    inline=False,
                )
            embed.set_image(url=DEFAULT_IMAGE_URL)
            embed.set_footer(
                text=f"📄 Page {self.page + 1} of {self.max_page + 1} • ☀️ {len(self.commands)} commands"
            )

            self.add_navigation_buttons()
            await self.message.edit(embed=embed, view=self)
        except Exception as e:
            espeon_log(
                tag="error", message=f"[PaginatedCategoryView] send_page failed: {e}"
            )


# 💠───────────────────────────────────────────────────────────────
# [🔘 BUTTONS] Navigation
# ────────────────────────────────────────────────────────────────
class PageNavButton(discord.ui.Button):
    def __init__(self, emoji, view, direction):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
        self.view_ref = view
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.user:
            return await interaction.response.send_message(
                "This menu isn't for you! ❌", ephemeral=True
            )
        await interaction.response.defer()
        self.view_ref.page += self.direction
        await self.view_ref.send_page()


class BackHomeButton(discord.ui.Button):
    def __init__(self, user, command_map):
        super().__init__(emoji="🏠", style=discord.ButtonStyle.primary)
        self.user = user
        self.command_map = command_map

    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user != self.user:
                return await interaction.response.send_message(
                    "This menu isn’t for you! ❌", ephemeral=True
                )

            view = CommandCategoryMenuView(self.user, self.command_map or {})
            description = (
                "Choose a command group by clicking the buttons below! ☀️\n\n"
                + "\n".join(view.category_lines)
            )

            embed = discord.Embed(
                title=f"{Espeon_Emoji.purple_flower} Command Categories",
                description=description,
                color=EMBED_COLOR,
            )
            embed.set_image(url=DEFAULT_IMAGE_URL)
            embed.set_thumbnail(url=DEFAULT_THUMBNAIL)
            embed.set_author(
                name=self.user.display_name, icon_url=self.user.display_avatar.url
            )

            view.message = interaction.message
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            espeon_log(tag="error", message=f"[BackHomeButton] Callback failed: {e}")


# 💠───────────────────────────────────────────────────────────────
# [🌼 VIEW] Category Menu — Home
# ────────────────────────────────────────────────────────────────
class CommandCategoryMenuView(discord.ui.View):
    def __init__(self, user: discord.User, command_map: dict[str, list[str]]):
        super().__init__(timeout=120)
        self.user = user
        self.command_map = command_map
        self.message: discord.Message = None
        self.category_lines = []

        for category, data in CATEGORY_CONFIG.items():
            emoji = data["emoji"]
            if command_map.get(category):
                self.add_item(
                    CategoryButton(user, category, command_map[category], command_map)
                )
                self.category_lines.append(f"{emoji} — {data['label']} Commands")


class CategoryButton(discord.ui.Button):
    def __init__(self, user, category, commands_list, command_map):
        config = CATEGORY_CONFIG[category]
        super().__init__(emoji=config["emoji"], style=discord.ButtonStyle.secondary)
        self.user = user
        self.category = category
        self.commands = commands_list
        self.command_map = command_map

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "This menu isn’t for you! ❌", ephemeral=True
            )
        await interaction.response.defer()

        view = PaginatedCategoryView(
            self.user, self.category, self.commands, self.command_map
        )
        view.message = interaction.message
        await view.send_page()


# 💠───────────────────────────────────────────────────────────────
# [📚 COG] CommandsView
# ────────────────────────────────────────────────────────────────
class CommandsView(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="commands", description="View Espeon's commands!")
    @espeon_roles_only()
    async def commands(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)

            user = interaction.user

            # Flatten commands
            all_commands = flatten_commands(self.bot.tree.get_commands())
            command_map = {"Public": [], "Owner": []}

            for cmd in all_commands:
                category = getattr(cmd, "extras", {}).get("category", "Public")

                # 👑 Owner-only
                if category == "Owner":
                    if user.id == OWNER_ID:
                        command_map["Owner"].append(cmd)
                else:
                    command_map["Public"].append(cmd)

            view = CommandCategoryMenuView(user, command_map)
            description = (
                "Choose a command group by clicking the buttons below! ☀️\n\n"
                + "\n".join(view.category_lines)
            )

            embed = discord.Embed(
                title=f"{Espeon_Emoji.purple_flower} Command Categories",
                description=description,
                color=EMBED_COLOR,
            )
            embed.set_image(url=DEFAULT_IMAGE_URL)
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=DEFAULT_THUMBNAIL)
            view.message = await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            espeon_log(tag="error", message=f"[CommandsView] Command failed: {e}")


# 💠───────────────────────────────────────────────────────────────
# [📦 SETUP]
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    try:
        await bot.add_cog(CommandsView(bot))
        # pretty_log("info", "🐭 CommandsView cog loaded successfully!")
    except Exception as e:
        espeon_log(tag="critical", message=f"Failed to load CommandsView cog: {e}")
