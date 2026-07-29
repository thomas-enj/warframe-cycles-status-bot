import asyncio
from utils import (
    fetch_json,
    format_remaining_from_iso,
    iso_to_unix,
    send_discord_patch,
)


async def update_duviri_channel(env):
    """Updates the Duviri & Zariman Discord channel embed."""
    duviri, zariman = await asyncio.gather(
        fetch_json("https://api.warframestat.us/pc/duviriCycle"),
        fetch_json("https://api.warframestat.us/pc/zarimanCycle"),
    )

    emotion_en = {
        "joy": "Joy 😊",
        "sorrow": "Sorrow 😢",
        "anger": "Anger 😡",
        "envy": "Envy 🟢",
        "fear": "Fear 😱",
    }

    # Dictionary of the logical sequence of the spiral
    emotion_next = {
        "joy": "Anger 😡",
        "anger": "Sorrow 😢",
        "sorrow": "Fear 😱",
        "fear": "Envy 🟢",
        "envy": "Joy 😊",
    }

    fields = []

    def add_spacer():
        fields.append({
            "name": "\u200b",
            "value": "\u200b",
            "inline": False,
        })

    # 🌀 Duviri
    d_expiry = duviri.get("expiry")
    d_ts = iso_to_unix(d_expiry)
    d_remaining = format_remaining_from_iso(d_expiry)
    d_state_raw = str(duviri.get("state", "")).lower()
    d_state = emotion_en.get(d_state_raw, d_state_raw.capitalize())
    d_next = emotion_next.get(d_state_raw, "Unknown")
    fields.append({
        "name": "🌀 Duviri Spiral",
        "value": (
            f"Mood: **{d_state}**\n"
            f"Next: **{d_next}** {d_remaining} (<t:{d_ts}:R>)"
        ),
        "inline": False,
    })
    add_spacer()

    # 🚢 Zariman
    z_expiry = zariman.get("expiry")
    z_ts = iso_to_unix(z_expiry)
    z_remaining = format_remaining_from_iso(z_expiry)
    is_corpus = zariman.get("isCorpus")
    z_state = "Corpus 🔷" if zariman.get("isCorpus") else "Grineer 🔴"
    z_next = "Grineer 🔴" if is_corpus else "Corpus 🔷"
    fields.append({
        "name": "🚢 Zariman Ten-Zero",
        "value": (
            f"Occupant: **{z_state}**\n"
            f"Next: **{z_next}** {z_remaining} (<t:{z_ts}:R>)\n\u200b"
        ),
        "inline": False,
    })

    embed = {
        "title": "🌀 Warframe - Duviri & Zariman",
        "description": "\u200b",
        "color": 10181046,  # Purple
        "fields": fields,
        "footer": {
            "text": "Updated automatically via Cloudflare Workers"
        },
    }

    await send_discord_patch(
        env.DUVIRI_CHANNEL_ID,
        env.DUVIRI_MESSAGE_ID,
        env.DISCORD_TOKEN,
        embed,
    )
