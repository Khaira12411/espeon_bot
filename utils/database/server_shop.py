import random
import string
from typing import List

import asyncpg
import discord

from config.paldea_galar_dict import rarity_meta
from config.pokemons import *
from utils.loggers.espeon_log import EspeonContext, espeon_log


def format_item_name(item_name: str, dex: str = None) -> str:
    """
    Format the item name for display.
    """

    MEGA_ITEMS = ["mega mewtwo y"]
    if "coin" in item_name.lower():
        return item_name  # No special formatting for currency items

    rarity = None
    lower_name = item_name.lower()
    if "shiny mega " in lower_name or "smega " in lower_name:
        rarity = "shiny mega"
        item_name = item_name.replace("Shiny Mega ", "").replace("SMega ", "")
    elif "shiny gigantamax" in lower_name:
        rarity = "shiny gigantamax"
        item_name = item_name.replace("Shiny Gigantamax ", "")
    elif "shiny " in lower_name:
        rarity = "shiny"
        item_name = item_name.replace("Shiny ", "")
    elif "golden mega " in lower_name or "gmega " in lower_name:
        rarity = "golden mega"
        item_name = item_name.replace("Golden Mega ", "").replace("GMega ", "")

    elif "golden " in lower_name:
        rarity = "golden"
        item_name = item_name.replace("Golden ", "")
    elif lower_name in legendary_mons:
        rarity = "legendary"
    elif lower_name in superrare_mons:
        rarity = "superrare"
    elif lower_name in uncommon_mons:
        rarity = "uncommon"
    elif lower_name in common_mons:
        rarity = "common"

    elif "gigantamax" in lower_name:
        rarity = "gmax"
        item_name = item_name.replace("Gigantamax ", "")

    elif lower_name in MEGA_ITEMS or "mega " in lower_name:
        rarity = "mega"
        item_name = item_name.replace("Mega ", "")

    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "") if rarity else ""
    display_name = (
        f"{rarity_emoji} {item_name.title()}" if rarity_emoji else item_name.title()
    )
    has_dex = False
    if dex and dex != "N/A":
        has_dex = True
    display_name = f"{display_name} #{dex}" if has_dex else display_name
    return display_name


def generate_item_id(length=8):
    """Generate a random alphanumeric item_id of given length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


async def box_item_autocomplete(
    interaction: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    """
    Autocomplete for box items from the database.
    Choice.name = "Item Name"
    Choice.value = "item_name"
    Matches both names and item IDs.
    """
    from utils.cache.server_shop_cache import fetch_all_box_items

    try:
        items = fetch_all_box_items()
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch box items from cache: {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        items = {}
    current = (current or "").lower().strip()
    results: List[discord.app_commands.Choice[str]] = []
    for item_id, item in items.items():
        item_name = str(item.get("item_name", "Unnamed Item"))
        if (
            not current
            or current in item_name.lower()
            or current in str(item_id).lower()
        ):
            results.append(discord.app_commands.Choice(name=item_name, value=item_name))
        if len(results) >= 25:
            break
    if not results:
        results.append(discord.app_commands.Choice(name="No matches found", value=""))
    return results


async def shop_item_autocomplete(
    interaction: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    """
    Autocomplete for server shop items from cache.
    Choice.name = "Item Name"
    Choice.value = "item_name"
    Matches both names and item IDs.
    """
    from utils.cache.server_shop_cache import fetch_all_shop_items

    try:
        items = fetch_all_shop_items()
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch shop items from cache: {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        items = {}

    current = (current or "").lower().strip()
    results: List[discord.app_commands.Choice[str]] = []

    for item_id, item in items.items():
        item_name = str(item.get("item_name", "Unnamed Item"))
        if (
            not current
            or current in item_name.lower()
            or current in str(item_id).lower()
        ):
            results.append(discord.app_commands.Choice(name=item_name, value=item_name))
        if len(results) >= 25:
            break

    if not results:
        results.append(discord.app_commands.Choice(name="No matches found", value=""))

    return results


# -------------------- Server Shop Database Functions --------------------


async def upsert_item(
    bot: discord.Client,
    item_name: str,
    price: int,
    stock: int,
    image_link: str,
    description: str = None,
    dex: str = None,
) -> str:
    """
    Insert or update an item by name in the server_shop table.
    If the item already exists (by name), update its price and stock.
    If not, insert a new item with a generated item_id.
    Returns the item_id used.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            # Try to fetch existing item_id by name
            row = await conn.fetchrow(
                "SELECT item_id FROM server_shop WHERE item_name = $1;", item_name
            )
            if row:
                item_id = row["item_id"]
            else:
                item_id = generate_item_id()

            await conn.execute(
                """
                INSERT INTO server_shop (item_name, price, stock, item_id, image_link, description, dex)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (item_id)
                DO UPDATE SET item_name = EXCLUDED.item_name, price = EXCLUDED.price, stock = EXCLUDED.stock, image_link = EXCLUDED.image_link, description = EXCLUDED.description, dex = EXCLUDED.dex;
                """,
                item_name,
                price,
                stock,
                item_id,
                image_link,
                description,
                dex,
            )
            espeon_log(
                tag="db",
                message=f"Upserted item '{item_name}' (item_id: {item_id}, price: {price}, stock: {stock}, dex: {dex})",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
            # Upsert in cache as well
            from utils.cache.server_shop_cache import upsert_shop_item

            upsert_shop_item(
                item_id, item_name, price, stock, image_link, description, dex
            )

        return item_id
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to upsert item '{item_name}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        return None


async def remove_item_by_name(bot: discord.Client, item_name: str) -> None:
    """
    Remove an item by name from the server_shop table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM server_shop WHERE item_name = $1;", item_name
            )
            espeon_log(
                tag="db",
                message=f"Removed item '{item_name}' from shop.",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

            # Remove from cache as well
            from utils.cache.server_shop_cache import remove_shop_item_by_name

            remove_shop_item_by_name(item_name)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove item '{item_name}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )


async def remove_item(bot: discord.Client, item_id: str) -> None:
    """
    Remove an item by item_id from the server_shop table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM server_shop WHERE item_id = $1;", item_id)
            espeon_log(
                tag="db",
                message=f"Removed item with item_id '{item_id}' from shop.",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

            # Remove from cache as well
            from utils.cache.server_shop_cache import remove_shop_item

            remove_shop_item(item_id)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove item with item_id '{item_id}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )


async def update_price(bot: discord.Client, item_id: str, price: int) -> None:
    """
    Update the price of an item in the server_shop table by item_id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_shop SET price = $1 WHERE item_id = $2;",
                price,
                item_id,
            )
            espeon_log(
                tag="db",
                message=f"Updated price for item_id '{item_id}' to {price}.",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
            # Update in cache as well
            from utils.cache.server_shop_cache import update_price_in_cache

            update_price_in_cache(item_id, price)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update price for item_id '{item_id}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )


async def update_stock(bot: discord.Client, item_id: str, stock: int) -> None:
    """
    Update the stock of an item in the server_shop table by item_id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE server_shop SET stock = $1 WHERE item_id = $2;",
                stock,
                item_id,
            )
            espeon_log(
                tag="db",
                message=f"Updated stock for item_id '{item_id}' to {stock}.",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

            # Update in cache as well
            from utils.cache.server_shop_cache import update_stock_in_cache

            update_stock_in_cache(item_id, stock)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update stock for item_id '{item_id}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )


async def update_item(
    bot: discord.Client,
    item_id: str,
    item_name: str = None,
    price: int = None,
    stock: int = None,
    image_link: str = None,
):
    """
    Update multiple fields of an item in the server_shop table by item_id."""

    try:
        async with bot.pg_pool.acquire() as conn:
            fields = []
            values = []
            if item_name is not None:
                fields.append("item_name = $" + str(len(values) + 1))
                values.append(item_name)
            if price is not None:
                fields.append("price = $" + str(len(values) + 1))
                values.append(price)
            if stock is not None:
                fields.append("stock = $" + str(len(values) + 1))
                values.append(stock)
            if image_link is not None:
                fields.append("image_link = $" + str(len(values) + 1))
                values.append(image_link)
            if not fields:
                return  # Nothing to update
            values.append(item_id)
            query = f"UPDATE server_shop SET {', '.join(fields)} WHERE item_id = ${len(values)};"
            await conn.execute(query, *values)
            espeon_log(
                tag="db",
                message=f"Updated item with item_id '{item_id}': {fields}",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

            # Update in cache as well
            from utils.cache.server_shop_cache import update_shop_item_in_cache

            update_shop_item_in_cache(item_id, item_name, price, stock, image_link)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update item with item_id '{item_id}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )


async def remove_all_items(bot: discord.Client) -> None:
    """
    Remove all items from the server_shop table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM server_shop;")
            espeon_log(
                tag="db",
                message="Removed all items from server_shop.",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

            # Clear cache as well
            from utils.cache.cache_list import server_shop_cache

            server_shop_cache.clear()
            espeon_log(
                tag="cache",
                message="Cleared server shop cache after removing all items.",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove all items: {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )


async def fetch_all_items(bot: discord.Client):
    """
    Fetch all items from the server_shop table.
    Returns a list of records.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM server_shop;")
            espeon_log(
                tag="db",
                message=f"Fetched all items from server_shop ({len(rows)} items).",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
            return rows
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch all items: {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        return []


async def fetch_item_by_id(bot: discord.Client, item_id: str):
    """
    Fetch a single item by item_id from the server_shop table.
    Returns the record or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM server_shop WHERE item_id = $1;", item_id
            )
            espeon_log(
                tag="db",
                message=f"Fetched item with item_id '{item_id}' from server_shop: {row}",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
            return row
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch item with item_id '{item_id}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        return None


async def fetch_item_by_name(bot: discord.Client, item_name: str):
    """
    Fetch a single item by name from the server_shop table.
    Returns the record or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM server_shop WHERE item_name = $1;", item_name
            )
            espeon_log(
                tag="db",
                message=f"Fetched item '{item_name}' from server_shop: {row}",
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
            return row
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch item '{item_name}': {e}",
            exc=e,
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        return None
