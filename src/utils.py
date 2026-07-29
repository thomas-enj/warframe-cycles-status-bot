import json
from datetime import datetime, timezone
from js import Object, fetch
from pyodide.ffi import to_js


def py_to_js(obj):
    """Converts Python dictionaries and lists to native JS Objects for fetch."""
    return to_js(obj, dict_converter=Object.fromEntries)


async def fetch_json(url: str) -> dict:
    """Queries an external API and returns a Python dictionary."""
    res = await fetch(url)
    js_obj = await res.json()
    return js_obj.to_py()


def iso_to_unix(iso_str: str) -> int:
    """Converts an ISO 8601 string to a Unix timestamp for Discord."""
    if not iso_str:
        return 0
    clean_iso = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_iso)
    return int(dt.timestamp())


def format_remaining_from_iso(iso_str: str) -> str:
    """Formats remaining duration using natural English hour/minute labels."""
    if not iso_str:
        return "unknown"

    clean_iso = iso_str.replace("Z", "+00:00")
    expiry = datetime.fromisoformat(clean_iso)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    total_seconds = int((expiry - now).total_seconds())

    if total_seconds <= 0:
        return "now"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    hour_word = "hour" if hours == 1 else "hours"
    minute_word = "minute" if minutes == 1 else "minutes"
    second_word = "second" if seconds == 1 else "seconds"

    if hours > 0:
        if minutes > 0:
            if hours == 1 and minutes == 1:
                return " in 1 hour and 1 minute"
            return f" in {hours} {hour_word} {minutes} {minute_word}"
        return f" in {hours} {hour_word}"
    if minutes > 0:
        return f" in {minutes} {minute_word}"
    return f" in {seconds} {second_word}"


async def send_discord_patch(
    channel_id: str, message_id: str, token: str, embed: dict
):
    """Sends a PATCH request to the Discord REST API to edit a message."""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"

    if not token:
        print("❌ Error: DISCORD_TOKEN is empty or missing!")
        return

    print(f"🔍 DEBUG: DISCORD_TOKEN loaded (length: {len(token)} characters)")

    payload = {
        "method": "PATCH",
        "headers": {
            "Authorization": f"Bot {token.strip()}",
            "Content-Type": "application/json",
        },
        "body": json.dumps({"content": "", "embeds": [embed]}),
    }

    # Convert Python payload to native JavaScript object
    js_options = py_to_js(payload)

    res = await fetch(url, js_options)

    if not res.ok:
        error_text = await res.text()
        print(
            f"❌ Discord API Error ({res.status}) for Channel {channel_id}: {error_text}"
        )
    else:
        print(f"✅ Successfully updated message in channel {channel_id}")
