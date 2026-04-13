# 🟣────────────────────────────────────────────
#       💜 MR Weakness User Settings DB 💜
# ─────────────────────────────────────────────


# -------------------------- Fetch All User Settings --------------------------
async def fetch_all_mr_user_settings(bot):
    """
    Fetch all users’ Mr. Weakness display settings.
    Returns a list of dicts: [{user_id: int, user_name: str, display_type: str}, ...]
    """
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, user_name, display_type FROM mr_user_weakness_settings"
        )
    return [dict(row) for row in rows]


# -------------------------- Update / Insert User Setting --------------------------
async def upsert_mr_user_setting(bot, user_id: int, user_name: str, display_type: str):
    """
    Insert or update a user's Mr. Weakness settings.
    display_type can be 'truncated' or 'full'.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO mr_user_weakness_settings (user_id, user_name, display_type, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET user_name = $2, display_type = $3, updated_at = NOW()
            """,
            user_id,
            user_name,
            display_type,
        )
        # Upsert in cache as well
        from utils.cache.mr_weakness_cache import insert_mr_user
        insert_mr_user(user_id, user_name, display_type)

async def update_user_name(bot, user_id: int, new_user_name: str):
    """
    Update a user's name in the database when they change their Discord username.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE mr_user_weakness_settings
            SET user_name = $1, updated_at = NOW()
            WHERE user_id = $2
            """,
            new_user_name,
            user_id,
        )
        # Also update in cache
        from utils.cache.mr_weakness_cache import get_mr_user, insert_mr_user
        existing = get_mr_user(user_id)
        if existing:
            insert_mr_user(user_id, new_user_name, existing["display_type"])