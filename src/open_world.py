import asyncio
from utils import (
    fetch_json,
    format_remaining_from_iso,
    send_discord_patch,
)


def _format_vallis_state(vallis: dict) -> str:
    """Returns a stable Orb Vallis state label from available API fields."""
    is_warm = vallis.get("isWarm")
    if isinstance(is_warm, bool):
        return "Warm 🔥" if is_warm else "Cold ❄️"

    state_raw = str(vallis.get("state", "")).strip().lower()
    if state_raw == "warm":
        return "Warm 🔥"
    if state_raw == "cold":
        return "Cold ❄️"
    return state_raw.capitalize() if state_raw else "Unknown"


def _format_cambion_state(cambion: dict) -> str:
    """Returns Cambion Drift state using canonical cycle names."""
    state_raw = str(cambion.get("state", "")).strip().lower()
    state_map = {
        "fass": "Fass 🔴",
        "vome": "Vome 🔵",
    }
    fallback = state_raw.capitalize() if state_raw else "Unknown"
    return state_map.get(state_raw, fallback)


async def update_open_world_channel(env):
    """Updates the Open World Discord channel embed."""
    cetus, vallis, cambion = await asyncio.gather(
        fetch_json("https://api.warframestat.us/pc/cetusCycle"),
        fetch_json("https://api.warframestat.us/pc/vallisCycle"),
        fetch_json("https://api.warframestat.us/pc/cambionCycle"),
    )

    fields = []

    def add_spacer():
        fields.append({
            "name": "\u200b",
            "value": "\u200b",
            "inline": False,
        })

    # 🌄 Cetus
    c_expiry = cetus.get("expiry")
    c_remaining = format_remaining_from_iso(c_expiry)
    is_day = cetus.get("isDay")
    c_state = "Day ☀️" if is_day else "Night 🌙"
    c_next = "Night 🌙" if is_day else "Day ☀️"
    fields.append({
        "name": "🌄 Cetus (Plains of Eidolon)",
        "value": (
            f"State: **{c_state}**\n"
            f"Next: **{c_next}**  {c_remaining}"
        ),
        "inline": False,
    })
    add_spacer()

    # ❄️ Fortuna
    v_expiry = vallis.get("expiry")
    v_remaining = format_remaining_from_iso(v_expiry)
    v_state = _format_vallis_state(vallis)
    v_next = "Cold ❄️" if "Warm" in v_state else "Warm 🔥"
    fields.append({
        "name": "❄️ Fortuna (Orb Vallis)",
        "value": (
            f"State: **{v_state}**\n"
            f"Next: **{v_next}**  {v_remaining}"
        ),
        "inline": False,
    })
    add_spacer()

    # 🦠 Deimos
    cb_expiry = cambion.get("expiry")
    cb_remaining = format_remaining_from_iso(cb_expiry)
    cb_active = _format_cambion_state(cambion)
    cb_next = "Vome 🔵" if "Fass" in cb_active else "Fass 🔴"
    fields.append({
        "name": "🦠 Deimos (Cambion Drift)",
        "value": (
            f"State: **{cb_active}**\n"
            f"Next: **{cb_next}**  {cb_remaining}\n\u200b"
        ),
        "inline": False,
    })

    embed = {
        "title": "⚔️ Warframe - Open Worlds",
        "description": "\u200b",
        "color": 3447003,  # Blue
        "fields": fields,
        "footer": {
            "text": "Updated automatically via Cloudflare Workers"
        },
    }

    await send_discord_patch(
        env.OPEN_WORLD_CHANNEL_ID,
        env.OPEN_WORLD_MESSAGE_ID,
        env.DISCORD_TOKEN,
        embed,
    )
