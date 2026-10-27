import os

import requests


WARFRAME_API_URL = "https://api.warframestat.us/pc/voidTrader"
DISCORD_API_URL = "https://discord.com/api/v10"
ACTIVE_COLOR = 15844367
INACTIVE_COLOR = 15158332


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is missing")
    return value


def main():

    is_active_value = required_env("BARO_ACTIVE").lower()
    if is_active_value not in {"true", "false"}:
        raise RuntimeError("BARO_ACTIVE must be 'true' or 'false'")
    is_active = is_active_value == "true"

    discord_token = required_env("DISCORD_TOKEN")
    channel_id = required_env("DISCORD_CHANNEL")
    message_id = required_env("BARO_MSG2_ID")
    message_url = (
        f"{DISCORD_API_URL}/channels/{channel_id}/messages/{message_id}"
    )
    headers = {"Authorization": f"Bot {discord_token}"}

    if is_active:
        print("Baro is present. Fetching his inventory...")
        response = requests.get(WARFRAME_API_URL, timeout=20)
        response.raise_for_status()
        inventory = response.json().get("inventory") or []

        item_lines = [
            f"- **{item.get('item', 'Unknown item')}** - "
            f"{item.get('ducats', '?')} Ducats / "
            f"{item.get('credits', '?')} Credits"
            for item in inventory
        ]
        description = "\n".join(item_lines)
        if not description:
            description = "Inventory is temporarily unavailable."
        if len(description) > 4096:
            description = description[:4093] + "..."

        embed = {
            "title": "Baro Ki'Teer's Inventory",
            "description": description,
            "color": ACTIVE_COLOR,
        }
    else:
        print("Baro has left. Marking the shop as closed...")
        embed = {
            "title": "The shop is closed",
            "description": "Baro Ki'Teer has returned to the Void.",
            "color": INACTIVE_COLOR,
        }

    response = requests.patch(
        message_url,
        headers=headers,
        json={"content": "", "embeds": [embed]},
        timeout=20,
    )
    response.raise_for_status()
    print("Successfully updated Baro's Discord message.")


if __name__ == "__main__":
    main()
