import discord

from utils.cache.cache_list import (
    catch_contest_event_cache,
    catch_contest_participants_cache,
)
from utils.database.catch_contest_db import (
    fetch_all_catch_contest_events,
    fetch_catch_contest_event,
    fetch_catch_contest_participants_by_id,
    fetch_all_catch_contest_participants
)
from utils.loggers.espeon_log import EspeonContext, espeon_log
# 💜────────────────────────────────────────────
#   🟣 Catch Contest Cache Manager 🟣
# 💜────────────────────────────────────────────

async def load_catch_contest_events_cache(bot: discord.Client):
    """
    Load all catch contest events from the database into the cache.
    """
    events = await fetch_all_catch_contest_events(bot)
    for event in events:
        catch_contest_event_cache[event["id"]] = {
            "pokemon": event.get("pokemon"),
            "catch_goal": event.get("catch_goal"),
            "ends_on": event.get("ends_on"),
        }

    espeon_log(
        tag="cache",
        message=f"Loaded {len(events)} catch contest events into cache",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )

    if catch_contest_event_cache:
        # Load  participants for all events
        await load_catch_contest_participants_cache(bot)

    return catch_contest_event_cache

def upsert_catch_contest_event(event_id: int, pokemon: str, catch_goal: int, ends_on):
    """Insert or update a catch contest event in cache."""
    catch_contest_event_cache[event_id] = {
        "pokemon": pokemon,
        "catch_goal": catch_goal,
        "ends_on": ends_on,
    }
    espeon_log(
        tag="cache",
        message=f"Inserted/Updated catch contest event '{event_id}' in cache (cache now {len(catch_contest_event_cache)} events)",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )

def update_catch_contest_event_in_cache(event_id: int, **kwargs):
    """Update fields of a catch contest event in cache."""
    if event_id in catch_contest_event_cache:
        for k, v in kwargs.items():
            if k in catch_contest_event_cache[event_id]:
                catch_contest_event_cache[event_id][k] = v
        espeon_log(
            tag="cache",
            message=f"Updated catch contest event '{event_id}' in cache with {kwargs}",
            label="🦩 CATCH CONTEST CACHE",
            context=EspeonContext.STRAYMONS,
        )

def remove_catch_contest_event_from_cache(event_id: int):
    """Remove a catch contest event from cache."""
    if event_id in catch_contest_event_cache:
        catch_contest_event_cache.pop(event_id)
        espeon_log(
            tag="cache",
            message=f"Removed catch contest event '{event_id}' from cache",
            label="🦩 CATCH CONTEST CACHE",
            context=EspeonContext.STRAYMONS,
        )
def remove_all_catch_contest_events_from_cache():
    """Clear all catch contest events from cache."""
    catch_contest_event_cache.clear()
    espeon_log(
        tag="cache",
        message=f"Cleared all catch contest events from cache",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )


def fetch_event_id_by_pokemon_from_cache(pokemon: str) -> int | None:
    """Fetch event_id by pokemon name from cache."""
    for event_id, event in catch_contest_event_cache.items():
        if event["pokemon"] == pokemon:
            return event_id
    return None


# 🟣────────────────────────────────────────────
#   💜 Catch Contest Participants Cache Manager 💜
# 🟣────────────────────────────────────────────

# Load all catch contest participants into cache
async def load_catch_contest_participants_cache(bot: discord.Client):
    """
    Load all catch contest participants from the database into the cache.
    """
    participants = await fetch_all_catch_contest_participants(bot)
    catch_contest_participants_cache.clear()
    for participant in participants:
        key = (participant["event_id"], participant["user_id"])
        catch_contest_participants_cache[key] = {
            "event_id": participant.get("event_id"),
            "user_id": participant.get("user_id"),
            "user_name": participant.get("user_name"),
            "pokemon": participant.get("pokemon"),
            "pokemon_caught": participant.get("pokemon_caught", 0),
        }

    espeon_log(
        tag="cache",
        message=f"Loaded {len(participants)} catch contest participants into cache",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )

    return catch_contest_participants_cache

async def load_single_catch_contest_participants_cache(bot: discord.Client, event_id: int):
    """
    Load catch contest participants for a specific event from the database into the cache.
    """
    participants = await fetch_catch_contest_participants_by_id(bot, event_id)
    for participant in participants:
        key = (participant["event_id"], participant["user_id"])
        catch_contest_participants_cache[key] = {
            "event_id": participant.get("event_id"),
            "user_id": participant.get("user_id"),
            "user_name": participant.get("user_name"),
            "pokemon": participant.get("pokemon"),
            "pokemon_caught": participant.get("pokemon_caught", 0),
        }

    espeon_log(
        tag="cache",
        message=f"Loaded {len(participants)} participants for event {event_id} into cache",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )

    return catch_contest_participants_cache

def upsert_catch_contest_participant(
    event_id: int,
    user_id: int,
    user_name: str,
    pokemon: str,
    pokemon_caught: int = 0,
):
    """Insert or update a catch contest participant in cache."""
    key = (event_id, user_id)
    catch_contest_participants_cache[key] = {
        "event_id": event_id,
        "user_id": user_id,
        "user_name": user_name,
        "pokemon": pokemon,
        "pokemon_caught": pokemon_caught,
    }
    espeon_log(
        tag="cache",
        message=f"Inserted/Updated participant '{user_name}' for event '{event_id}' in cache (cache now {len(catch_contest_participants_cache)} participants)",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )

def update_participant_caught_count_in_cache(event_id: int, user_id: int, caught_count: int):
    """Update the pokemon_caught count for a participant in cache."""
    key = (event_id, user_id)
    if key in catch_contest_participants_cache:
        catch_contest_participants_cache[key]["pokemon_caught"] = caught_count
        espeon_log(
            tag="cache",
            message=f"Updated caught count for participant '{user_id}' in event '{event_id}' to {caught_count} in cache",
            label="🦩 CATCH CONTEST CACHE",
            context=EspeonContext.STRAYMONS,
        )

def remove_catch_contest_participant_from_cache(event_id: int, user_id: int):
    """Remove a catch contest participant from cache."""
    key = (event_id, user_id)
    if key in catch_contest_participants_cache:
        catch_contest_participants_cache.pop(key)
        espeon_log(
            tag="cache",
            message=f"Removed participant '{user_id}' for event '{event_id}' from cache",
            label="🦩 CATCH CONTEST CACHE",
            context=EspeonContext.STRAYMONS,
        )

def remove_all_catch_contest_participants_of_event_from_cache(event_id: int):
    """Remove all participants of a specific event from cache."""
    keys_to_remove = [key for key in catch_contest_participants_cache if key[0] == event_id]
    for key in keys_to_remove:
        catch_contest_participants_cache.pop(key)
    espeon_log(
        tag="cache",
        message=f"Removed all participants for event '{event_id}' from cache",
        label="🦩 CATCH CONTEST CACHE",
        context=EspeonContext.STRAYMONS,
    )
