from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.aesthetic import Espeon_Emoji
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

        # If only one page, remove all buttons
        if self.max_page == 0:
            self.clear_items()

    @discord.ui.button(
        emoji=Espeon_Emoji.left_arrow, style=discord.ButtonStyle.secondary
    )
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You can't press this button.", ephemeral=True
            )
            return
        self.page -= 1
        if self.page < 0:
            self.page = self.max_page
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(
        emoji=Espeon_Emoji.right_arrow, style=discord.ButtonStyle.secondary
    )
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You can't press this button.", ephemeral=True
            )
            return
        self.page += 1
        if self.page > self.max_page:
            self.page = 0
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    async def update_buttons(self, interaction):
        # Disable left arrow on first page, enable otherwise
        for item in self.children:
            if (
                hasattr(item, "callback")
                and getattr(item.callback, "__name__", "") == "previous_page"
            ):
                item.disabled = self.page == 0
            if (
                hasattr(item, "callback")
                and getattr(item.callback, "__name__", "") == "next_page"
            ):
                item.disabled = self.page == self.max_page
        await interaction.message.edit(view=self)

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
            desc_line = item.get("description")
            if desc_line:
                desc_line_str = f"\n> - Description: {desc_line}"
            else:
                desc_line_str = ""

            embed.add_field(
                name=f"{number}. {display_item}",
                value=f"> - ID: {item_id}\n> - Price: {price} {CHERRY_PIN}\n> - Stock: {stock_display}{desc_line_str}",
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
    item_name: str = None,
):
    """
    View all items in the server shop.
    """

    if item_name:
        from utils.cache.server_shop_cache import fetch_shop_item_id_by_name
        item_id = fetch_shop_item_id_by_name(item_name)
        if item_id:
            item = server_shop_cache.get(item_id)
            if item:
                # Show single item embed
                display_item_name = format_item_name(item.get("item_name", "Unknown Item"))
                price = item.get("price", 0)
                stock = item.get("stock", 0)
                image_link = item.get("image_link", "")
                stock_display = "Unlimited" if stock == -1 else str(stock)
                description_line = item.get("description", "")

                embed = discord.Embed(
                    title=f"🌸 Petal Lace Shop 🌸",
                    color=COLOR,
                    timestamp=datetime.now(),
                )
                embed.set_image(url=DIVIDER)
                embed.add_field(
                    name=display_item_name,
                    value=(
                        f"> - ID: {item_id}\n"
                        f"> - Price: {price} {CHERRY_PIN}\n"
                        f"> - Stock: {stock_display}"
                        f"{f'\n> - Description: {description_line}' if description_line else ''}"
                    ),
                    inline=False,
                )
                guild = bot.get_guild(STRAYMONS_GUILD_ID)
                embed.set_footer(
                    text="🌸 Petal Lace Shop",
                    icon_url=guild.icon.url if guild and guild.icon else None,
                )
                if image_link:
                    embed.set_thumbnail(url=image_link)

                # Defer
                loader = await pretty_defer(
                    interaction=interaction,
                    content="Fetching server shop item...",
                    ephemeral=False,
                )
                await loader.success(embed=embed, content="")
                return
    else:
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

        # Sort items by cheapest price first, then alphabetically by item name
        items.sort(
            key=lambda x: (x.get("price", float("inf")), x.get("item_name", "").lower())
        )

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
