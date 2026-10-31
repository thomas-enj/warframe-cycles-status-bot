import os

import requests


WARFRAME_API_URL = "https://api.warframestat.us/pc/voidTrader"
DISCORD_API_URL = "https://discord.com/api/v10"
ACTIVE_COLOR = 15844367
INACTIVE_COLOR = 15158332
INVENTORY_CATEGORIES = (
    "Mods",
    "Appearance",
    "Weapons",
    "Miscellaneous",
)
APPEARANCE_PATHS = (
    "/skins/",
    "/avatarimages/",
    "/sigils/",
    "/emblems/",
    "/shipdecos/",
    "/actionfiguredioramas/",
    "/accessories/",
    "/catbrows/",
    "/plushies/",
)


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
        embeds = [build_inventory_embed(inventory)]
    else:
        print("Baro has left. Marking the shop as closed...")
        embeds = [{
            "title": "The shop is closed",
            "description": "Baro Ki'Teer has returned to the Void.",
            "color": INACTIVE_COLOR,
        }]

    response = requests.patch(
        message_url,
        headers=headers,
        json={"content": "", "embeds": embeds},
        timeout=20,
    )
    response.raise_for_status()
    print("Successfully updated Baro's Discord message.")


def inventory_category(item):
    unique_name = item.get("uniqueName", "").lower()

    is_mod = "/upgrades/mods/" in unique_name
    is_peculiar_mod = "/cosmeticenhancers/peculiars/" in unique_name
    if is_mod or is_peculiar_mod:
        return "Mods"
    if "/weapons/" in unique_name:
        return "Weapons"
    if any(path in unique_name for path in APPEARANCE_PATHS):
        return "Appearance"
    if "ephemera" in unique_name or "ephemera" in item.get("item", "").lower():
        return "Appearance"
    return "Miscellaneous"


def build_inventory_embed(inventory):
    grouped_items = {category: [] for category in INVENTORY_CATEGORIES}
    for item in inventory:
        category = inventory_category(item)
        item_line = (
            f"- **{item.get('item', 'Unknown item')}** - "
            f"{_format_number(item.get('ducats'))} Ducats / "
            f"{_format_number(item.get('credits'))} Credits"
        )
        grouped_items[category].append(item_line)

    title = "Baro Ki'Teer's Inventory"
    description_parts = []
    description_length = 0
    included_items = 0
    description_limit = 3900
    overflow = False

    for category, item_lines in grouped_items.items():
        if not item_lines:
            continue

        heading = f"**{category}**"
        heading_prefix = "\n\n" if description_parts else ""
        heading_text = f"{heading_prefix}{heading}"
        if description_length + len(heading_text) + 1 > description_limit:
            overflow = True
            break

        description_parts.append(heading_text)
        description_length += len(heading_text)
        for line in item_lines:
            item_text = f"\n{line}"
            if description_length + len(item_text) > description_limit:
                overflow = True
                break
            description_parts.append(item_text)
            description_length += len(item_text)
            included_items += 1
        if overflow:
            break

    total_items = sum(len(lines) for lines in grouped_items.values())
    if not description_parts:
        description = "Inventory is temporarily unavailable."
    else:
        description = "".join(description_parts)

    omitted_items = total_items - included_items
    if omitted_items:
        description += (
            f"\n\n*{omitted_items} more items omitted due to Discord's "
            "embed size limit.*"
        )

    return {
        "title": title,
        "description": description,
        "color": ACTIVE_COLOR,
    }


def _format_number(value):
    if isinstance(value, int):
        return f"{value:,}"
    return str(value) if value is not None else "?"


if __name__ == "__main__":
    main()
