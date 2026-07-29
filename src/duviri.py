import asyncio
from utils import fetch_json, iso_to_unix, send_discord_patch


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

    fields = []

    def add_spacer():
        fields.append({
            "name": "\u200b",
            "value": "\u200b",
            "inline": False,
        })

    # 🌀 Duviri
    d_ts = iso_to_unix(duviri.get("expiry"))
    d_state_raw = str(duviri.get("state", "")).lower()
    d_state = emotion_en.get(d_state_raw, d_state_raw.capitalize())
    fields.append({
        "name": "🌀 Duviri Spiral",
        "value": f"Mood: **{d_state}**\nChanges <t:{d_ts}:R>",
        "inline": False,
    })
    add_spacer()

    # 🚢 Zariman
    z_ts = iso_to_unix(zariman.get("expiry"))
    z_state = "Corpus 🔷" if zariman.get("isCorpus") else "Grineer 🔴"
    fields.append({
        "name": "🚢 Zariman Ten-Zero",
        "value": f"Occupant: **{z_state}**\nChanges <t:{z_ts}:R>\n\u200b",
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
