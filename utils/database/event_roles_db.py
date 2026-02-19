import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log

# SQL SCRIPT
"""CREATE TABLE event_roles (
    role_id BIGINT NOT NULL,
    role_name TEXT,
    user_id BIGINT NOT NULL,
    user_name TEXT,
    PRIMARY KEY (role_id, user_id)
);"""


async def upsert_user_w_role(bot, role_id, role_name, user_id, user_name):
    """
    Add or update a user's event role in the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO event_roles (role_id, role_name, user_id, user_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (role_id, user_id) DO UPDATE
                SET role_name = EXCLUDED.role_name,
                    user_name = EXCLUDED.user_name;
                """,
                role_id,
                role_name,
                user_id,
                user_name,
            )
    except Exception as e:
        espeon_log(
            "error",
            f"Error upserting event role for user {user_name} (ID: {user_id}) and role {role_name} (ID: {role_id}): {e}",
            source="Event Roles Database",
        )


async def fetch_all_users_w_role(bot: discord.Client, role_id):
    """
    Fetch all users with a specific event role.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name FROM event_roles
                WHERE role_id = $1;
                """,
                role_id,
            )
            return [(row["user_id"], row["user_name"]) for row in rows]
    except Exception as e:
        espeon_log(
            "error",
            f"Error fetching users with event role ID {role_id}: {e}",
            source="Event Roles Database",
        )
        return []


async def remove_user_w_role(bot: discord.Client, role_id, user_id):
    """
    Remove a user's event role from the database.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM event_roles
                WHERE role_id = $1 AND user_id = $2;
                """,
                role_id,
                user_id,
            )
    except Exception as e:
        espeon_log(
            "error",
            f"Error removing event role ID {role_id} for user ID {user_id}: {e}",
            source="Event Roles Database",
        )
