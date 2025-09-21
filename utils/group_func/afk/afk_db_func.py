from utils.loggers.espeon_log import EspeonContext, espeon_log

# 🌙────────────────────────────────────────────
#   AFK Database Functions (Espeon Logging)
# 🌙────────────────────────────────────────────

# 💙────────────────────────────────────────────
#   Upsert AFK
# 💙────────────────────────────────────────────
async def upsert_afk(
    bot, user_id: int, user_name: str, reason: str | None, started_at: int
):
    """
    Insert or update AFK row for a user.
    """
    from utils.cache.afk_user_cache import afk_cache_upsert

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO afk_status (user_id, user_name, reason, started_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    reason = EXCLUDED.reason,
                    started_at = EXCLUDED.started_at
                """,
                user_id,
                user_name,
                reason,
                started_at,
            )

        # 🟣 Keep cache in sync
        afk_cache_upsert(
            {
                "user_id": user_id,
                "user_name": user_name,
                "reason": reason,
                "started_at": started_at,
            }
        )

        espeon_log(
            tag="db",
            message=f"[💙 AFK] Upserted AFK for **{user_name}** "
            f"(reason: {reason}) → ✅ updated in DB + cache",
            context=EspeonContext.STRAYMONS,
        )
        return
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to upsert AFK for **{user_name}**: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return


# 🤍────────────────────────────────────────────
#   Update AFK Reason
# 🤍────────────────────────────────────────────
async def update_afk_reason(
    bot, user_id: int, user_name: str, reason: str | None
) -> bool:
    """
    Update only the AFK reason for a user.
    """
    from utils.cache.afk_user_cache import afk_cache_update_reason

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE afk_status SET reason = $2 WHERE user_id = $1", user_id, reason
            )
            afk_cache_update_reason(user_id=user_id, new_reason=reason)

        espeon_log(
            tag="db",
            message=f"[🤍 AFK] Updated AFK reason for **{user_name}** → {reason} "
            f"→ ✅ updated in DB + cache",
            context=EspeonContext.STRAYMONS,
        )
        return
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to update AFK reason for **{user_name}**: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return


# 💙────────────────────────────────────────────
#   Clear AFK
# 💙────────────────────────────────────────────
async def clear_afk(bot, user_id: int, user_name: str):
    """
    Remove AFK row for a user.
    """
    from utils.cache.afk_user_cache import afk_cache_remove

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM afk_status WHERE user_id = $1", user_id)
            afk_cache_remove(user_id=user_id)

        espeon_log(
            tag="db",
            message=f"[💙 AFK] Cleared AFK for **{user_name}** "
            f"→ ✅ removed from DB + cache",
            context=EspeonContext.STRAYMONS,
        )
        return
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to clear AFK for **{user_name}**: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return


# 🤍────────────────────────────────────────────
#   Fetch AFK
# 🤍────────────────────────────────────────────
async def fetch_afk(bot, user_id: int, user_name: str) -> dict | None:
    """
    Fetch AFK row for a user.
    """

    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM afk_status WHERE user_id = $1", user_id
            )
        if row:
            espeon_log(
                tag="db",
                message=f"[🤍 AFK] Fetched AFK row for **{user_name}**",
                context=EspeonContext.STRAYMONS,
            )
            return dict(row)
        return None
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to fetch AFK for **{user_name}**: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return None


# 💙────────────────────────────────────────────
#   Fetch All AFKs
# 💙────────────────────────────────────────────
async def fetch_all_afk(bot) -> list[dict]:
    """
    Fetch all AFK rows.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM afk_status")
        espeon_log(
            tag="db",
            message=f"[💙 AFK] Fetched all AFK rows (count={len(rows)})",
            context=EspeonContext.STRAYMONS,
        )
        return [dict(row) for row in rows]
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"[💜 AFK] Failed to fetch all AFKs: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return []
