from typing import Any, Dict, Optional

import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log

# SQL Script
"""CREATE TABLE clan_promo_item (
    promo_name TEXT NOT NULL,
    user_id INT NOT NULL,
    user_name TEXT,
    drops INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (promo_name, user_id)
);
"""


async def fetch_all_member_promo_items(bot: discord.Client) -> list[Dict[str, Any]]:
    """
    Fetch all member promo item drops for the single active promo.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT i.promo_name, i.user_id, i.user_name, i.drops, i.updated_at
                FROM clan_promo_item AS i
                INNER JOIN clan_promo_events AS e
                    ON i.promo_name = e.name
                WHERE e.id = 1
                ORDER BY i.drops DESC, i.updated_at DESC
                """)
            return [dict(row) for row in rows]
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to fetch all member promo items for active promo: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return []


async def upsert_member_promo_item(
    bot: discord.Client,
    promo_name: str,
    user_id: int,
    user_name: str,
    drops: int = 0,
):
    """
    Upsert a member's promo item into the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO clan_promo_item (promo_name, user_id, user_name, drops)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (promo_name, user_id) DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    drops = EXCLUDED.drops,
                    updated_at = NOW()
                """,
                promo_name,
                user_id,
                user_name,
                drops,
            )
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to upsert member promo item {promo_name} for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )


async def delete_member_promo_item(bot: discord.Client, promo_name: str, user_id: int):
    """
    Delete a member's promo item from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM clan_promo_item
                WHERE promo_name = $1 AND user_id = $2
                """,
                promo_name,
                user_id,
            )
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to delete member promo item {promo_name} for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )


async def delete_all_member_promo_items(bot: discord.Client, promo_name: str):
    """
    Delete all member promo items for a specific promo from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM clan_promo_item
                WHERE promo_name = $1
                """,
                promo_name,
            )
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to delete all member promo items for promo {promo_name}: {e}",
            context=EspeonContext.STRAYMONS,
        )


async def get_member_promo_item(
    bot: discord.Client, promo_name: str, user_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get a member's promo item from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM clan_promo_item
                WHERE promo_name = $1 AND user_id = $2
                """,
                promo_name,
                user_id,
            )
            if row:
                return dict(row)
            return None
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to get member promo item {promo_name} for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return None
