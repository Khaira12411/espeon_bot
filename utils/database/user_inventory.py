import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log

# SQL SCRIPT
"""CREATE TABLE user_inventory (
    user_id BIGINT,
    user_name TEXT,
    item_name TEXT,
    stock INTEGER,
    image_link TEXT,
    PRIMARY KEY (user_id, item_name)
);"""


async def upsert_user_inventory(
    bot,
    user_id: int,
    user_name: str,
    item_name: str,
    stock: int = 1,
    image_link: str = None,
):
    """Upserts or updates a user's inventory item in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                    INSERT INTO user_inventory (user_id, user_name, item_name, stock, image_link)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id, item_name) DO UPDATE
                    SET stock = EXCLUDED.stock,
                        image_link = EXCLUDED.image_link,
                        user_name = EXCLUDED.user_name;
                    """,
                user_id,
                user_name,
                item_name,
                stock,
                image_link,
            )
            espeon_log(
                tag="db",
                message=f"Upserted inventory for user '{user_name}' - Item: '{item_name}', Stock: {stock}",
                label="🧑‍🛒 USER INVENTORY",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to upsert inventory for user '{user_name}' - Item: '{item_name}': {e}",
            exc=e,
        )


async def fetch_item_from_inventory(bot, user_id: int, item_name: str):
    """Fetches a specific item from a user's inventory in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT item_name, stock, image_link
                FROM user_inventory
                WHERE user_id = $1 AND item_name = $2;
                """,
                user_id,
                item_name,
            )
            if row:
                item_data = {
                    "item_name": row["item_name"],
                    "stock": row["stock"],
                    "image_link": row["image_link"],
                }
                espeon_log(
                    tag="db",
                    message=f"Fetched item '{item_name}' for user_id {user_id}: {item_data}",
                    label="🧑‍🛒 USER INVENTORY",
                    context=EspeonContext.ESPEON,
                )
                return item_data
            else:
                espeon_log(
                    tag="db",
                    message=f"Item '{item_name}' not found for user_id {user_id}.",
                    label="🧑‍🛒 USER INVENTORY",
                    context=EspeonContext.ESPEON,
                )
                return None
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch item '{item_name}' for user_id {user_id}: {e}",
            exc=e,
        )
        


async def get_user_inventory(bot, user_id: int):
    """Fetches a user's inventory from the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT item_name, stock, image_link
                FROM user_inventory
                WHERE user_id = $1;
                """,
                user_id,
            )
            inventory = [
                {
                    "item_name": row["item_name"],
                    "stock": row["stock"],
                    "image_link": row["image_link"],
                }
                for row in rows
            ]
            espeon_log(
                tag="db",
                message=f"Fetched inventory for user_id {user_id}: {inventory}",
                label="🧑‍🛒 USER INVENTORY",
                context=EspeonContext.ESPEON,
            )
            return inventory
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch inventory for user_id {user_id}: {e}",
            exc=e,
        )
        return []


async def update_stock(bot, user_id: int, item_name: str, new_stock: int):
    """Updates the stock of a specific item in a user's inventory."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_inventory
                SET stock = $1
                WHERE user_id = $2 AND item_name = $3;
                """,
                new_stock,
                user_id,
                item_name,
            )
            espeon_log(
                tag="db",
                message=f"Updated stock for user_id {user_id} - Item: '{item_name}' to {new_stock}",
                label="🧑‍🛒 USER INVENTORY",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update stock for user_id {user_id} - Item: '{item_name}': {e}",
            exc=e,
        )


async def remove_item(bot, user_id: int, item_name: str):
    """Removes an item from a user's inventory in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM user_inventory
                WHERE user_id = $1 AND item_name = $2;
                """,
                user_id,
                item_name,
            )
            espeon_log(
                tag="db",
                message=f"Removed item '{item_name}' from inventory of user_id {user_id}",
                label="🧑‍🛒 USER INVENTORY",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove item '{item_name}' from inventory of user_id {user_id}: {e}",
            exc=e,
        )


async def clear_inventory(bot, user_id: int):
    """Clears all items from a user's inventory in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM user_inventory
                WHERE user_id = $1;
                """,
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"Cleared inventory for user_id {user_id}",
                label="🧑‍🛒 USER INVENTORY",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to clear inventory for user_id {user_id}: {e}",
            exc=e,
        )


async def clear_all_inventories(bot):
    """Clears all inventories for all users in the database."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM user_inventory;
                """,
            )
            espeon_log(
                tag="db",
                message=f"Cleared all user inventories",
                label="🧑‍🛒 USER INVENTORY",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to clear all user inventories: {e}",
            exc=e,
        )
