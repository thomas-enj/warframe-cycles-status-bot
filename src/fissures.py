from utils import fetch_json, iso_to_unix, send_discord_patch


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
    expiry = iso_to_unix(fissure.get("expiry"))
    remaining = f"<t:{expiry}:R>" if expiry else "unknown expiration"

    return f"• **{tier}** · {mission_type} — {node} · {remaining}"


def _build_fissures_embed(fissures: list) -> dict:
    grouped = {"normal": [], "steel_path": [], "railjack": []}
    for fissure in fissures:
        grouped[_fissure_column(fissure)].append(_format_fissure(fissure))

    columns = (
        ("normal", "Standard Fissures"),
        ("steel_path", "Steel Path"),
        ("railjack", "Railjack"),
    )
    fields = [
        {
            "name": name,
            "value": "\n".join(grouped[key]) or "No active fissures",
            "inline": True,
        }
        for key, name in columns
    ]

    return {
        "title": "Warframe — Void Fissures",
        "description": (
            "Active missions for opening Void Relics."
        ),
        "color": 3447003,
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
