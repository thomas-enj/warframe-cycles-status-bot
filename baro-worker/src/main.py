import json
from datetime import datetime, timezone

from js import Date, Headers, Intl, Object, Request, fetch
from pyodide.ffi import to_js


WARFRAME_API_URL = "https://api.warframestat.us/pc/voidTrader"
DISCORD_API_URL = "https://discord.com/api/v10"
GITHUB_API_URL = "https://api.github.com"
ACTIVE_COLOR = 15844367
INACTIVE_COLOR = 15158332


async def on_scheduled(event, env, ctx=None):
    response = await fetch(WARFRAME_API_URL)
    if not response.ok:
        raise RuntimeError(f"Warframe API returned HTTP {response.status}")

    data = (await response.json()).to_py()
    inventory = data.get("inventory") or []
    is_active = len(inventory) > 0
    location = data.get("location") or "Unknown relay"
    activation = _discord_timestamp(data.get("activation"))
    expiry = _discord_timestamp(data.get("expiry"))

    if is_active:
        status_text = (
            "**Baro Ki'Teer is currently here!**\n"
            f"📍 **Location:** {location}\n"
            f"⏳ **Leaves:** {_format_countdown(expiry)} "
            f"({_format_paris_datetime(expiry)})"
        )
    else:
        status_text = (
            "**Baro Ki'Teer is currently absent.**\n\n"
            f"📍 **Next location:** {location}\n"
            f"⏳ **Arrives:** {_format_countdown(activation)} "
            f"({_format_paris_datetime(activation)})"
        )

    status_text += "\n\n\u200b"
    await update_status_message(env, status_text)
    previous_state = await get_inventory_message_state(env)
    if previous_state is None or previous_state != is_active:
        await trigger_github_action(
            env.GITHUB_TOKEN, env.GITHUB_REPO, is_active
        )


def _discord_timestamp(value):
    if not value:
        raise ValueError("Warframe API response is missing a Baro date")
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _format_countdown(target_timestamp):
    remaining = max(
        0,
        target_timestamp - int(datetime.now(timezone.utc).timestamp()),
    )
    if remaining == 0:
        return "now"

    for seconds_per_unit, unit in (
        (86400, "day"),
        (3600, "hour"),
        (60, "minute"),
    ):
        if remaining >= seconds_per_unit:
            amount = (remaining + seconds_per_unit - 1) // seconds_per_unit
            plural = "s" if amount != 1 else ""
            return f"in {amount} {unit}{plural}"

    return "in less than a minute"


def _format_paris_datetime(target_timestamp):
    options = to_js(
        {
            "weekday": "long",
            "month": "long",
            "day": "numeric",
            "year": "numeric",
            "hour": "numeric",
            "minute": "2-digit",
            "timeZone": "Europe/Paris",
            "timeZoneName": "shortOffset",
        },
        dict_converter=Object.fromEntries,
    )
    formatter = Intl.DateTimeFormat.new("en-US", options)
    formatted = str(formatter.format(Date.new(target_timestamp * 1000)))
    return formatted.replace("GMT", "UTC")


def _discord_headers(token):
    return _headers({
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    })


def _headers(values):
    js_values = to_js(values, dict_converter=Object.fromEntries)
    return Headers.new(js_values)


async def update_status_message(env, content):
    url = (
        f"{DISCORD_API_URL}/channels/{env.DISCORD_CHANNEL}/"
        f"messages/{env.BARO_MSG1_ID}"
    )
    request = Request.new(
        url,
        method="PATCH",
        headers=_discord_headers(env.DISCORD_TOKEN),
        body=json.dumps({"content": content, "embeds": []}),
    )
    response = await fetch(request)
    if not response.ok:
        error_text = await response.text()
        raise RuntimeError(
            f"Discord status-message update failed ({response.status}): "
            f"{error_text}"
        )


async def get_inventory_message_state(env):
    url = (
        f"{DISCORD_API_URL}/channels/{env.DISCORD_CHANNEL}/"
        f"messages/{env.BARO_MSG2_ID}"
    )
    request = Request.new(
        url, method="GET", headers=_discord_headers(env.DISCORD_TOKEN)
    )
    response = await fetch(request)
    if not response.ok:
        error_text = await response.text()
        raise RuntimeError(
            f"Discord inventory-message lookup failed ({response.status}): "
            f"{error_text}"
        )

    message = (await response.json()).to_py()
    embeds = message.get("embeds") or []
    if not embeds:
        return None

    color = embeds[0].get("color")
    if color == ACTIVE_COLOR:
        return True
    if color == INACTIVE_COLOR:
        return False
    return None


async def trigger_github_action(token, repo, is_active):
    url = f"{GITHUB_API_URL}/repos/{repo}/dispatches"
    headers = _headers({
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "baro-tracker-worker",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    payload = json.dumps({
        "event_type": "update_baro_inventory",
        "client_payload": {"is_active": is_active},
    })
    request = Request.new(url, method="POST", headers=headers, body=payload)
    response = await fetch(request)
    if not response.ok:
        error_text = await response.text()
        raise RuntimeError(
            f"GitHub dispatch failed ({response.status}): {error_text}"
        )