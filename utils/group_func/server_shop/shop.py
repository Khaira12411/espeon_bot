from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.current_setup import STRAYMONS_GUILD_ID
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from utils.cache.cache_list import server_shop_cache
from utils.database.server_shop import fetch_all_items, format_item_name
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ PAGINATED SHOP VIEW       🩷
# 🌸───────────────────────────────────────────────🌸
class Shop_Paginator(View):
    def __init__(self, bot, user, items, per_page=10, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.items = items
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(items) - 1) // per_page
        self.message: discord.Message | None = None  # Store the sent message

        # If only one page, remove buttons
        if self.max_page == 0:
            self.clear_items()  # remove all buttons

    # Don't put previous if on first page
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You can't press this button.", ephemeral=True
            )
            return
        self.page -= 1
        if self.page < 0:
            self.page = self.max_page

        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You can't press this button.", ephemeral=True
            )
            return
        self.page += 1
        if self.page > self.max_page:
            self.page = 0

        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    async def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_items = self.items[start:end]

        title = "🌸 Petal Lace Shop 🌸"
        description = "Welcome to the Petal Lace Shop — where your Cherry Pins bloom into exclusive treasures."
        embed = discord.Embed(
            title=title, description=description, color=COLOR, timestamp=datetime.now()
        )
        embed.set_image(url=DIVIDER)
        for idx, item in enumerate(page_items):
            number = idx + 1 + start
            item_id = item.get("item_id", 0)
            item_name = item.get("item_name", "Unknown Item")
            price = item.get("price", 0)
            stock = item.get("stock", 0)
            stock_display = "Unlimited" if stock == -1 else str(stock)
            display_item = format_item_name(item_name)
            embed.add_field(
                name=f"{number}. {display_item}",
                value=f"> - ID: {item_id}\n> - Price: {price} {CHERRY_PIN}\n> - Stock: {stock_display}",
                inline=False,
            )
        total_items = len(self.items)
        footer_text = (
            f"Total Items: {total_items} | "
            f"Page {self.page + 1} of {self.max_page + 1}"
        )
        guild = self.bot.get_guild(STRAYMONS_GUILD_ID)
        # Set guild icon as footer icon if available
        embed.set_footer(
            text=footer_text, icon_url=guild.icon.url if guild and guild.icon else None
        )
        return embed


async def shop_view_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    View all items in the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction,
        content="Fetching server shop items...",
        ephemeral=False,
    )
    # Fetch all items from db
    items = await fetch_all_items(bot=bot)
    if not items:
        await loader.error("The server shop is currently empty.")
        return

    # Sort items by cheapest price first
    items.sort(key=lambda x: x.get("price", float("inf")))

    # Sort it by cheapest first

    # Create paginator
    paginator = Shop_Paginator(
        bot=bot,
        user=interaction.user,
        items=items,
        per_page=10,
    )
    embed = await paginator.get_embed()

    sent_message = await loader.success(embed=embed, content="", view=paginator)
    paginator.message = sent_message
