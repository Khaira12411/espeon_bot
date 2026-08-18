from typing import Any, Dict, Optional

import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log


async def fetch_active_promo(bot: discord.Client) -> Optional[Dict[str, Any]]:
    """
    Fetch the single active promo from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM clan_promo_events LIMIT 1")
            return dict(row) if row else None
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to fetch active promo: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return None


async def fetch_promo(bot: discord.Client, name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a promo by name.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM clan_promo_events WHERE name = $1", name
            )
            return dict(row) if row else None
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to fetch promo {name}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return None


async def upsert_promo(
    bot: discord.Client,
    name: str,
    prize: str,
    image_url: str,
    emoji: str,
    catch_rate: str,
    battle_rate: str,
    fish_rate: str,
    whitelist_role_id: Optional[int] = None,
    number_before_claim: int = 0,
    ends_on: Optional[int] = None,
):
    """
    Upsert the single active promo into the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO clan_promo_events (
                    name, prize, image_url, emoji, catch_rate, battle_rate, fish_rate,
                    whitelist_role_id, number_before_claim, ends_on
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (name) DO UPDATE SET
                    prize = EXCLUDED.prize,
                    image_url = EXCLUDED.image_url,
                    emoji = EXCLUDED.emoji,
                    catch_rate = EXCLUDED.catch_rate,
                    battle_rate = EXCLUDED.battle_rate,
                    fish_rate = EXCLUDED.fish_rate,
                    whitelist_role_id = EXCLUDED.whitelist_role_id,
                    number_before_claim = EXCLUDED.number_before_claim,
                    ends_on = EXCLUDED.ends_on,
                    updated_at = NOW()
                """,
                name,
                prize,
                image_url,
                emoji,
                catch_rate,
                battle_rate,
                fish_rate,
                whitelist_role_id,
                number_before_claim,
                ends_on,
            )
        espeon_log(
            "info",
            f"Upserted promo {name}",
            context=EspeonContext.STRAYMONS,
        )
        # Reload cache from DB so it includes id, updated_at, etc.
        from utils.cache.clan_promo_cache import load_active_promo_cache

        await load_active_promo_cache(bot)

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to upsert promo {name}: {e}",
            context=EspeonContext.STRAYMONS,
        )


async def delete_promo(bot: discord.Client, name: str):
    """
    Delete a promo by name.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM clan_promo_events WHERE name = $1", name)
        espeon_log(
            "info",
            f"Deleted promo {name}",
            context=EspeonContext.STRAYMONS,
        )
        from utils.cache.clan_promo_cache import delete_active_promo_cache

        delete_active_promo_cache()
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to delete promo {name}: {e}",
            context=EspeonContext.STRAYMONS,
        )


async def get_due_promo(bot: discord.Client) -> list[Dict[str, Any]]:
    """
    Get promos that are due (ends_on is not null and <= current unix time).
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM clan_promo_events WHERE ends_on IS NOT NULL AND ends_on <= EXTRACT(EPOCH FROM NOW())::INT"
            )
            return [dict(row) for row in rows]
    except Exception as e:
        espeon_log(
            "error", f"Failed to fetch due promos: {e}", context=EspeonContext.STRAYMONS
        )
        return []
