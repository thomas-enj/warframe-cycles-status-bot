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
            f"{item.get('ducats', '?'):,} Ducats / "
            f"{item.get('credits', '?'):,} Credits"
        )
        grouped_items[category].append(item_line)

    title = "Baro Ki'Teer's Inventory"
    fields = []
    total_chars = len(title) + 128
    omitted_items = 0
    stop_adding = False

    for category, item_lines in grouped_items.items():
        line_index = 0
        part = 1
        while line_index < len(item_lines) and len(fields) < 25:
            field_name = category
            if part > 1:
                field_name += f" (continued {part})"

            value_limit = min(896, 6000 - total_chars - len(field_name))
            if value_limit < 1:
                stop_adding = True
                break

            field_lines = []
            field_length = 0
            while line_index < len(item_lines):
                line = item_lines[line_index]
                added_length = len(line) + bool(field_lines)
                if field_length + added_length > value_limit:
                    break
                field_lines.append(line)
                field_length += added_length
                line_index += 1

            if not field_lines:
                stop_adding = True
                break

            value = "\n".join(field_lines)
            fields.append({
                "name": field_name,
                "value": value,
                "inline": False,
            })
            total_chars += len(field_name) + len(value)
            part += 1

        omitted_items += len(item_lines) - line_index
        if stop_adding or len(fields) >= 25:
            break

    total_items = sum(len(lines) for lines in grouped_items.values())
    included_items = sum(
        len(field["value"].splitlines()) for field in fields
    )
    omitted_items = total_items - included_items

    if omitted_items and fields:
        marker = (
            f"\n\n... {omitted_items} more items omitted "
            "by Discord's embed limits."
        )
        last_field = fields[-1]
        extra_chars = len(marker)
        if (
            len(last_field["value"]) + extra_chars <= 1024
            and total_chars - 128 + extra_chars <= 6000
        ):
            last_field["value"] += marker

    if not fields:
        return {
            "title": title,
            "description": "Inventory is temporarily unavailable.",
            "color": ACTIVE_COLOR,
        }
    return {"title": title, "color": ACTIVE_COLOR, "fields": fields}


if __name__ == "__main__":
    main()
