import asyncio
from utils import fetch_json, iso_to_unix, send_discord_patch


async def update_open_world_channel(env):
    """Updates the Open World Discord channel embed."""
    cetus, vallis, cambion = await asyncio.gather(
        fetch_json("https://api.warframestat.us/pc/cetusCycle"),
        fetch_json("https://api.warframestat.us/pc/vallisCycle"),
        fetch_json("https://api.warframestat.us/pc/cambionCycle"),
    )

    fields = []

    # 🌄 Cetus
    c_ts = iso_to_unix(cetus.get("expiry"))
    c_state = "Day ☀️" if cetus.get("isDay") else "Night 🌙"
    fields.append({
        "name": "🌄 Cetus (Plains of Eidolon)",
        "value": f"State: **{c_state}**\nChanges <t:{c_ts}:R>",
        "inline": True,
    })

    # ❄️ Fortuna
    v_ts = iso_to_unix(vallis.get("expiry"))
    v_state = "Warm 🔥" if vallis.get("isWarm") else "Cold ❄️"
    fields.append({
        "name": "❄️ Fortuna (Orb Vallis)",
        "value": f"State: **{v_state}**\nChanges <t:{v_ts}:R>",
        "inline": True,
    })

    # 🦠 Deimos
    cb_ts = iso_to_unix(cambion.get("expiry"))
    cb_active = cambion.get("active", "").capitalize()
    fields.append({
        "name": "🦠 Deimos (Cambion Drift)",
        "value": f"State: **{cb_active}**\nChanges <t:{cb_ts}:R>",
        "inline": True,
    })

    embed = {
        "title": "⚔️ Warframe - Open Worlds",
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