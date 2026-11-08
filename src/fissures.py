from utils import (
    fetch_json,
    format_discord_timestamp_from_iso,
    send_discord_patch,
)

_TIER_ORDER = {
    tier: index
    for index, tier in enumerate(
        ("Lith", "Meso", "Neo", "Axi", "Requiem", "Omnia")
    )
}


def _fissure_column(fissure: dict) -> str:
    if fissure.get("isStorm"):
        return "railjack"
    if fissure.get("isHard"):
        return "steel_path"
    return "normal"


def _format_fissure(fissure: dict) -> str:
    tier = fissure.get("tier") or "Unknown tier"
    mission_type = fissure.get("missionType") or "Unknown mission"
    node = fissure.get("node") or "Unknown node"
    expiry_timestamp = format_discord_timestamp_from_iso(
        fissure.get("expiry"), "Unknown time"
    )

    return f"**{tier}**\n{mission_type} · {node} · {expiry_timestamp}"


def _build_fissures_embed(fissures: list) -> dict:
    grouped = {"normal": [], "steel_path": [], "railjack": []}
    for fissure in fissures:
        grouped[_fissure_column(fissure)].append(fissure)

    columns = (
        ("normal", "Standard"),
        ("steel_path", "Steel Path"),
        ("railjack", "RailJack"),
    )
    fields = [
        {
            "name": name,
            "value": "\u200b\n" + (
                "\n\u200b\n".join(
                    _format_fissure(fissure)
                    for fissure in sorted(
                        grouped[key],
                        key=lambda item: _TIER_ORDER.get(
                            item.get("tier"), len(_TIER_ORDER)
                        ),
                    )
                )
                or "No active fissures"
            ),
            "inline": True,
        }
        for key, name in columns
    ]

    return {
        "title": "Void Fissures",
        "description": (
            "Active missions for opening Void Relics.\n\n\u200b"
        ),
        "color": 16777215,  # White color for fissures embed
        "fields": fields,
    }


async def update_fissures_channel(env):
    fissures = await fetch_json("https://api.warframestat.us/pc/fissures")
    embed = _build_fissures_embed(fissures)

    await send_discord_patch(
        env.FISSURE_CHANNEL_ID,
        env.FISSURE_MESSAGE_ID,
        env.DISCORD_TOKEN,
        embed,
    )
