# 🟣────────────────────────────────────────────
#       💜 MR Weakness User Settings DB 💜
# ─────────────────────────────────────────────

# -------------------------- Fetch All User Settings --------------------------
async def fetch_all_mr_user_settings(bot):
    """
    Fetch all users’ Mr. Weakness display settings.
    Returns a list of dicts: [{user_id: int, display_type: str}, ...]
    """
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, display_type FROM mr_user_weakness_settings"
        )
    return [dict(row) for row in rows]


# -------------------------- Update / Insert User Setting --------------------------
async def upsert_mr_user_setting(bot, user_id: int, display_type: str):
    """
    Insert or update a user's Mr. Weakness display_type.
    display_type can be 'truncated' or 'full'.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO mr_user_weakness_settings (user_id, display_type, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET display_type = $2, updated_at = NOW()
            """,
            user_id,
            display_type,
        )
