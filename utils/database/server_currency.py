import asyncpg
import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log


async def fetch_all_user_balances(bot: discord.Client) -> list[asyncpg.Record]:
    """Fetch all user balances from the server_currency table."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, user_name, cherry_pin_balance, bought_daisyia_box, bought_gardelette_box, bought_melaryne_box FROM server_currency;"
            )
            espeon_log(
                tag="db",
                message=f"Fetched all user balances from server_currency table (total {len(rows)} users)",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            return rows
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to fetch all user balances: {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )
        return []


async def bought_box(bot: discord.Client, user_id: int, box_type: str):
    """Mark that a user has bought a specific box."""
    box_type = box_type.lower()
    valid_boxes = ["daisyia box", "gardelette box", "melaryne box"]
    if box_type not in valid_boxes:
        espeon_log(
            tag="warn",
            message=f"⚠️ Invalid box type '{box_type}' provided for user_id '{user_id}'",
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )
        return
    # Map box type to column name
    box_type = box_type.replace(" ", "_")
    column_name = f"bought_{box_type}_box"

    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE server_currency
                SET {column_name} = 'yes'
                WHERE user_id = $1;
                """,
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"Marked user_id '{user_id}' as having bought the '{box_type}' box",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            # Update cache as well
            from utils.cache.user_balance_cache import bought_box_in_cache
            bought_box_in_cache(user_id, box_type)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to mark box purchase for user_id '{user_id}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )


async def upsert_user_balance(
    bot: discord.Client, user_id: int, user_name: str, amount: int = 0
):
    bought_daisyia_box = "no"
    bought_gardelette_box = "no"
    bought_melaryne_box = "no"

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_currency (user_id, user_name, cherry_pin_balance, bought_daisyia_box, bought_gardelette_box, bought_melaryne_box)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id)
                DO UPDATE SET user_name = EXCLUDED.user_name, cherry_pin_balance = EXCLUDED.cherry_pin_balance;
                """,
                user_id,
                user_name,
                amount,
                bought_daisyia_box,
                bought_gardelette_box,
                bought_melaryne_box,
            )
            espeon_log(
                tag="db",
                message=f"Upserted user '{user_name}' (user_id: {user_id}) with balance {amount}",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            # Upsert into cache as well
            from utils.cache.user_balance_cache import upsert_user_balance_in_cache

            upsert_user_balance_in_cache(
                user_id,
                user_name,
                amount,
                bought_daisyia_box,
                bought_gardelette_box,
                bought_melaryne_box,
            )

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to upsert user '{user_name}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )


async def get_user_balance(bot: discord.Client, user_id: int) -> int | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT cherry_pin_balance FROM server_currency WHERE user_id = $1;",
                user_id,
            )
            if row:
                return row["cherry_pin_balance"]
            else:
                return None
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to get balance for user_id '{user_id}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )
        return None


async def update_user_balance(
    bot: discord.Client, user_id: int, user_name: str, new_balance: int
):
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE server_currency
                SET cherry_pin_balance = $1
                WHERE user_id = $2;
                """,
                new_balance,
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"Updated balance for '{user_name}' to {new_balance}",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            # Update cache as well
            from utils.cache.user_balance_cache import update_user_balance_in_cache

            update_user_balance_in_cache(user_id, user_name, new_balance)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update balance for user_id '{user_id}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )


async def delete_user(bot: discord.Client, user_id: int, user_name: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM server_currency WHERE user_id = $1;",
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"Deleted '{user_name}' from server_currency",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            # Remove from cache as well
            from utils.cache.user_balance_cache import delete_user_balance_from_cache

            delete_user_balance_from_cache(user_id, user_name)
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to delete '{user_name}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )


async def reset_user_balance(bot: discord.Client, user_id: int, user_name: str):
    """Resets a user's balance to zero."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE server_currency
                SET cherry_pin_balance = 0
                WHERE user_id = $1;
                """,
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"Reset balance for '{user_name}' to 0",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            # Update cache as well
            from utils.cache.user_balance_cache import update_user_balance_in_cache

            update_user_balance_in_cache(user_id, user_name, 0)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to reset balance for '{user_name}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )


async def reset_all_balances(bot: discord.Client):
    """Clears all the rows in the server_currency table."""
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM server_currency;")
            espeon_log(
                tag="db",
                message="Cleared all rows in server_currency table.",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
            # Clear the cache as well
            from utils.cache.user_balance_cache import reset_all_user_balances_in_cache

            reset_all_user_balances_in_cache()

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to clear server_currency table: {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )
