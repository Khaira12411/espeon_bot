import asyncpg
import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log


async def upsert_user(bot: discord.Client, user_id: int, user_name: str):
    cherry_pin_balance = 0
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_currency (user_id, user_name, cherry_pin_balance)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET user_name = EXCLUDED.user_name;
                """,
                user_id,
                user_name,
                cherry_pin_balance,
            )
            espeon_log(
                tag="db",
                message=f"Upserted user '{user_name}' (user_id: {user_id}) with balance {cherry_pin_balance}",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
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


async def update_user_balance(bot: discord.Client, user_id: int, new_balance: int):
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
                message=f"Updated balance for user_id '{user_id}' to {new_balance}",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update balance for user_id '{user_id}': {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )


async def delete_user(bot: discord.Client, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM server_currency WHERE user_id = $1;",
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"Deleted user with user_id '{user_id}' from server_currency",
                label="💰 SERVER CURRENCY",
                context=EspeonContext.ESPEON,
            )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to delete user with user_id '{user_id}': {e}",
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
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to clear server_currency table: {e}",
            exc=e,
            label="💰 SERVER CURRENCY",
            context=EspeonContext.ESPEON,
        )
