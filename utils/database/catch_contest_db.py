import time

import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log


async def upsert_catch_contest_event(bot, pokemon, catch_goal, ends_on):
    """
    Insert a new catch contest event. ID will auto-increment.
    Returns the new event_id if successful, else None.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO catch_contest_event (pokemon, catch_goal, ends_on)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                pokemon,
                catch_goal,
                ends_on,
            )
            event_id = row["id"] if row else None
            espeon_log(
                tag="db",
                message=f"🟢 Inserted catch contest event for {pokemon} with goal {catch_goal} ending on {ends_on} (id={event_id})",
                label="🦩 CATCH CONTEST",
                context=EspeonContext.STRAYMONS,
            )

            # Upsert in cache as well
            from utils.cache.catch_contest_cache import upsert_catch_contest_event

            upsert_catch_contest_event(event_id, pokemon, catch_goal, ends_on)

            return event_id
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to insert catch contest event for {pokemon}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
            context=EspeonContext.STRAYMONS,
        )
        return None


async def update_catch_contest_event(bot, event_id, **kwargs):
    """
    Update fields of a catch contest event by id.
    kwargs can include: pokemon, catch_goal, ends_on
    """
    try:
        fields = []
        values = []
        for i, (k, v) in enumerate(kwargs.items(), start=1):
            fields.append(f"{k} = ${i+1}")
            values.append(v)
        if not fields:
            return False
        query = f"UPDATE catch_contest_event SET {', '.join(fields)} WHERE id = $1"
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, event_id, *values)
            espeon_log(
                tag="db",
                message=f"🟡 Updated catch contest event {event_id} with {kwargs}",
                label="🦩 CATCH CONTEST",
            )
            # Also update in cache
            from utils.cache.catch_contest_cache import (
                update_catch_contest_event_in_cache,
            )

            update_catch_contest_event_in_cache(event_id, **kwargs)

            return True

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update catch contest event {event_id}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )
        return False


async def remove_catch_contest_event(bot, event_id):
    """
    Remove a catch contest event by id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM catch_contest_event WHERE id = $1", event_id
            )
            espeon_log(
                tag="db",
                message=f"🔴 Removed catch contest event {event_id}",
                label="🦩 CATCH CONTEST",
            )

            # Also remove from cache
            from utils.cache.catch_contest_cache import (
                remove_catch_contest_event_from_cache,
            )

            remove_catch_contest_event_from_cache(event_id)
            return True
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove catch contest event {event_id}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )
        return False


async def fetch_all_catch_contest_events(bot):
    """
    Fetch all catch contest events.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM catch_contest_event")
            return [dict(row) for row in rows]
    except Exception as e:
        return []


async def fetch_catch_contest_event(bot, event_id):
    """
    Fetch a single catch contest event by id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM catch_contest_event WHERE id = $1", event_id
            )
            return dict(row) if row else None
    except Exception as e:
        return None


async def remove_all_catch_contest_events(bot):
    """
    Remove all catch contest events (clear the table).
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM catch_contest_event")
            espeon_log(
                tag="db",
                message="🔴 Removed all catch contest events",
                label="🦩 CATCH CONTEST",
            )
            # Also clear cache
            from utils.cache.catch_contest_cache import (
                remove_all_catch_contest_events_from_cache,
            )

            remove_all_catch_contest_events_from_cache()

            return True
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove all catch contest events: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )


async def fetch_expired_catch_contest_events(bot):
    """
    Fetch all catch contest events whose ends_on is less than the current unix time.
    """
    try:
        now = int(time.time())
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM catch_contest_event WHERE ends_on IS NOT NULL AND ends_on < $1",
                now,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        return []


# Catch contest participants functions


# Upsert participant
async def upsert_catch_contest_participant(bot, event_id, user_id, user_name, pokemon):
    """
    Upsert a catch contest participant.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO catch_contest_participants (event_id, user_id, user_name, pokemon)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (event_id, user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    pokemon = EXCLUDED.pokemon
                """,
                event_id,
                user_id,
                user_name,
                pokemon,
            )
            espeon_log(
                tag="db",
                message=f"🟢 Upserted participant {user_name} for event {event_id}",
                label="🦩 CATCH CONTEST",
            )
            # upsert in cache as well
            from utils.cache.catch_contest_cache import upsert_catch_contest_participant

            upsert_catch_contest_participant(event_id, user_id, user_name, pokemon)

            return True
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to upsert participant {user_name} for event {event_id}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )
        return False


async def update_participant_caught_count(bot, event_id, user_id, caught_count):
    """
    Update the pokemon_caught count for a participant.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE catch_contest_participants
                SET pokemon_caught = $1
                WHERE event_id = $2 AND user_id = $3
                """,
                caught_count,
                event_id,
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"🟡 Updated caught count for participant {user_id} in event {event_id} to {caught_count}",
                label="🦩 CATCH CONTEST",
            )
            # Update in cache as well
            from utils.cache.catch_contest_cache import (
                update_participant_caught_count_in_cache,
            )

            update_participant_caught_count_in_cache(event_id, user_id, caught_count)
            return True

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to update caught count for participant {user_id} in event {event_id}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )
        return False


async def fetch_catch_contest_participants_by_id(bot, event_id):
    """
    Fetch all participants for a given catch contest event.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM catch_contest_participants WHERE event_id = $1",
                event_id,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        return []


async def fetch_all_catch_contest_participants(bot):
    """
    Fetch all participants for all catch contest events.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM catch_contest_participants")
            return [dict(row) for row in rows]
    except Exception as e:
        return []


async def remove_catch_contest_participant(bot, event_id, user_id, user_name):
    """
    Remove a participant from a catch contest event.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM catch_contest_participants WHERE event_id = $1 AND user_id = $2",
                event_id,
                user_id,
            )
            espeon_log(
                tag="db",
                message=f"🔴 Removed participant {user_name} from event {event_id}",
                label="🦩 CATCH CONTEST",
            )
            # Also remove from cache
            from utils.cache.catch_contest_cache import (
                remove_catch_contest_participant_from_cache,
            )

            remove_catch_contest_participant_from_cache(event_id, user_id)
            return True
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove participant {user_name} from event {event_id}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )
        return False


async def remove_all_catch_contest_participants_of_event(bot, event_id):
    """
    Remove all participants from a specific catch contest event.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM catch_contest_participants WHERE event_id = $1",
                event_id,
            )
            espeon_log(
                tag="db",
                message=f"🔴 Removed all participants from event {event_id}",
                label="🦩 CATCH CONTEST",
            )
            # Also remove from cache
            from utils.cache.catch_contest_cache import (
                remove_all_catch_contest_participants_of_event_from_cache,
            )

            remove_all_catch_contest_participants_of_event_from_cache(event_id)
            return True
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove all participants from event {event_id}: {e}",
            exc=e,
            label="🦩 CATCH CONTEST",
        )
