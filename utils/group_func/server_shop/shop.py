import datetime
import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from utils.cache.cache_list import server_shop_cache
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log

async def shop_view_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    View all items in the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Fetching server shop items...", ephemeral=True
    )

    if not server_shop_cache:
        # try to load cache if empty
        from utils.cache.server_shop_cache import load_server_shop_cache
        await load_server_shop_cache(bot)

    if not server_shop_cache:
        await loader.error(content="The server shop is currently empty.")
        return

    # Sort it by cheapest first
    sorted_items = sorted(
        server_shop_cache.items(), key=lambda x: x[1]["price"]
    )

    # Build embed
    title = "🌸 Petal Lace Shop 🌸"
    description = "Welcome to the Petal Lace Shop — where your Cherry Pins bloom into exclusive treasures."
    embed = discord.Embed(title=title, description=description, color=COLOR, timestamp=datetime.now())
    embed.set_image(url=DIVIDER)
    for item_id, item in sorted_items:
        item_name = item.get("item_name", "Unknown Item")
        price = item.get("price", 0)
        stock = item.get("stock", 0)
        stock_display = "Unlimited" if stock == -1 else str(stock)
        embed.add_field(
            name=f"{item_name} (ID: `{item_id}`)",
            value=f"> - Price: {price} {CHERRY_PIN}\n> - Stock: {stock_display}",
            inline=False,
        )

    await loader.success(embed=embed, content="")
    espeon_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) viewed the server shop "
            f"with {len(server_shop_cache)} items."
        ),
        label="🛒 SERVER SHOP",
        context=EspeonContext.ESPEON,
    )