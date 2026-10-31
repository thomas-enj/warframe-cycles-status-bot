import os

import requests


WARFRAME_API_URL = "https://api.warframestat.us/pc/voidTrader"
DISCORD_API_URL = "https://discord.com/api/v10"
ACTIVE_COLOR = 15844367
INACTIVE_COLOR = 15158332
INVENTORY_CATEGORIES = (
    "Mods",
    "Appearance | Warframe Skin",
    "Appearance | Weapon Skin",
    "Appearance | Archwing Skin",
    "Appearance | Landing Craft Skin",
    "Appearance | Armor",
    "Appearance | Operator",
    "Appearance | Companion",
    "Appearance | Decorations",
    "Appearance | Glyphs & Emblems",
    "Appearance | Accessories",
    "Appearance | Ephemera",
    "Appearance | Other",
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
        content = "# Baro Ki'Teer's Inventory"
        embeds = build_inventory_embeds(inventory)
    else:
        print("Baro has left. Marking the shop as closed...")
        content = ""
        embeds = [{
            "title": "The shop is closed",
            "description": "Baro Ki'Teer has returned to the Void.",
            "color": INACTIVE_COLOR,
        }]

    response = requests.patch(
        message_url,
        headers=headers,
        json={"content": content, "embeds": embeds},
        timeout=20,
    )
    response.raise_for_status()
    print("Successfully updated Baro's Discord message.")


def inventory_category(item):
    unique_name = item.get("uniqueName", "").lower()
    item_name = item.get("item", "").lower()

    is_mod = "/upgrades/mods/" in unique_name
    is_peculiar_mod = "/cosmeticenhancers/peculiars/" in unique_name
    if is_mod or is_peculiar_mod:
        return "Mods"
    is_weapon = "/storeitems/weapons/" in unique_name
    is_weapon_type = "/types/weapons/" in unique_name
    if is_weapon or is_weapon_type:
        return "Weapons"

    is_appearance = any(path in unique_name for path in APPEARANCE_PATHS)
    if not is_appearance:
        return "Miscellaneous"

    if "ephemera" in unique_name or "ephemera" in item_name:
        return "Appearance | Ephemera"
    if "immortal skin" in item_name or "/skins/warframe/" in unique_name:
        return "Appearance | Warframe Skin"
    if "archwing" in unique_name or "odonata" in item_name:
        return "Appearance | Archwing Skin"
    landing_craft_names = ("liset", "xiphos", "mantis", "scimitar")
    is_landing_craft = "/skins/liset/" in unique_name or any(
        craft in item_name for craft in landing_craft_names
    )
    if is_landing_craft:
        return "Appearance | Landing Craft Skin"
    is_companion_path = any(
        path in unique_name for path in ("/catbrows/", "/sentinels/")
    )
    is_companion_item = any(
        companion in item_name
        for companion in ("kavat", "kubrow", "sentinel", "moa")
    )
    if is_companion_path or is_companion_item:
        return "Appearance | Companion"
    if any(path in unique_name for path in ("/operator/", "/accessories/")):
        return "Appearance | Operator"
    if any(
        token in unique_name or token in item_name
        for token in ("/armor/", "armor", "armour", "pauldrons", "plates")
    ):
        return "Appearance | Armor"
    if any(
        path in unique_name
        for path in ("/shipdecos/", "/actionfiguredioramas/", "/plushies/")
    ):
        return "Appearance | Decorations"
    has_glyph_path = any(
        path in unique_name
        for path in ("/avatarimages/", "/sigils/", "/emblems/")
    )
    has_glyph_name = any(
        token in item_name for token in ("glyph", "emblem", "sigil", "badge")
    )
    if has_glyph_path or has_glyph_name:
        return "Appearance | Glyphs & Emblems"
    is_accessory = any(
        token in item_name for token in ("syandana", "sugatra", "earpiece")
    )
    if is_accessory:
        return "Appearance | Accessories"
    if "skin" in item_name or "/skins/" in unique_name:
        return "Appearance | Weapon Skin"
    return "Appearance | Other"


def build_inventory_embeds(inventory):
    main_categories = ("Mods", "Appearance", "Weapons", "Miscellaneous")
    grouped_items = {category: [] for category in main_categories}
    for item in inventory:
        classification = inventory_category(item)
        if classification.startswith("Appearance | "):
            category = "Appearance"
            subcategory = classification.split(" | ", maxsplit=1)[1]
        else:
            category = classification
            subcategory = None
        item_line = (
            f"- **{item.get('item', 'Unknown item')}** - "
            f"{_format_number(item.get('ducats'))} Ducats / "
            f"{_format_number(item.get('credits'))} Credits"
        )
        grouped_items[category].append((subcategory, item_line))

    embeds = []
    total_embed_chars = 0
    included_items = 0
    total_items = len(inventory)

    for category, entries in grouped_items.items():
        if not entries:
            continue

        title = category
        available_chars = 6000 - total_embed_chars - len(title) - 128
        description_limit = min(3800, available_chars)
        if description_limit < 1:
            break

        if category == "Appearance":
            subcategories = tuple(
                category_name.split(" | ", maxsplit=1)[1]
                for category_name in INVENTORY_CATEGORIES
                if category_name.startswith("Appearance | ")
            )
            sections = [
                (
                    subcategory,
                    [
                        line
                        for item_subcategory, line in entries
                        if item_subcategory == subcategory
                    ],
                )
                for subcategory in subcategories
            ]
        else:
            sections = [(None, [line for _, line in entries])]

        description_parts = []
        description_length = 0
        category_item_count = 0
        category_overflow = False

        for subcategory, lines in sections:
            if not lines:
                continue
            if subcategory:
                heading_prefix = "\n\n" if description_parts else ""
                heading = f"{heading_prefix}**{subcategory}**"
                if description_length + len(heading) + 1 > description_limit:
                    category_overflow = True
                    break
                description_parts.append(heading)
                description_length += len(heading)

            for line in lines:
                item_text = f"\n{line}" if description_parts else line
                if description_length + len(item_text) > description_limit:
                    category_overflow = True
                    break
                description_parts.append(item_text)
                description_length += len(item_text)
                category_item_count += 1
            if category_overflow:
                break

        if description_parts:
            description = "".join(description_parts)
            embeds.append({
                "title": title,
                "description": description,
                "color": ACTIVE_COLOR,
            })
            total_embed_chars += len(title) + len(description)
            included_items += category_item_count

        if category_overflow:
            break

    omitted_items = total_items - included_items
    if omitted_items and embeds:
        marker = (
            f"\n\n*{omitted_items} more items omitted due to Discord's "
            "embed size limit.*"
        )
        last_embed = embeds[-1]
        if (
            len(last_embed["description"]) + len(marker) <= 4096
            and total_embed_chars + len(marker) <= 6000
        ):
            last_embed["description"] += marker

    if not embeds:
        return [{
            "title": "Inventory",
            "description": "Inventory is temporarily unavailable.",
            "color": ACTIVE_COLOR,
        }]
    return embeds


def _format_number(value):
    if isinstance(value, int):
        return f"{value:,}"
    return str(value) if value is not None else "?"


if __name__ == "__main__":
    main()
