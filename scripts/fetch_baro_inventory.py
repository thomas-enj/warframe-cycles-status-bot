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
        embeds = build_inventory_embeds(inventory)
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


def build_inventory_embeds(inventory):
    grouped_items = {category: [] for category in INVENTORY_CATEGORIES}
    for item in inventory:
        category = inventory_category(item)
        item_line = (
            f"**{item.get('item', 'Unknown item')}** - "
            f"{item.get('ducats', '?'):,} Ducats / "
            f"{item.get('credits', '?'):,} Credits"
        )
        grouped_items[category].append(item_line)

    embeds = []
    total_embed_chars = 0
    omitted_items = 0

    for category, item_lines in grouped_items.items():
        line_index = 0
        part = 1
        while line_index < len(item_lines) and len(embeds) < 10:
            title = f"Baro Ki'Teer's Inventory | {category}"
            if part > 1:
                title += f" (continued {part})"

            remaining_chars = 6000 - total_embed_chars - len(title)
            description_limit = min(4096, remaining_chars)
            if description_limit < 1:
                break

            description_lines = []
            description_length = 0
            while line_index < len(item_lines):
                line = item_lines[line_index]
                added_length = len(line) + bool(description_lines)
                if description_length + added_length > description_limit:
                    break
                description_lines.append(line)
                description_length += added_length
                line_index += 1

            if not description_lines:
                break

            description = "\n".join(description_lines)
            embeds.append({
                "title": title,
                "description": description,
                "color": ACTIVE_COLOR,
            })
            total_embed_chars += len(title) + len(description)
            part += 1

        omitted_items += len(item_lines) - line_index

    if omitted_items and embeds:
        marker = (
            f"\n\n... {omitted_items} more items omitted "
            "by Discord's embed limit."
        )
        last_embed = embeds[-1]
        extra_chars = len(marker)
        if (
            len(last_embed["description"]) + extra_chars <= 4096
            and total_embed_chars + extra_chars <= 6000
        ):
            last_embed["description"] += marker

    if not embeds:
        return [{
            "title": "Baro Ki'Teer's Inventory",
            "description": "Inventory is temporarily unavailable.",
            "color": ACTIVE_COLOR,
        }]
    return embeds


if __name__ == "__main__":
    main()
