import asyncio

from duviri import update_duviri_channel
from js import Response
from fissures import update_fissures_channel
from open_world import update_open_world_channel


async def _update_all_channels(env):
    updates = (
        ("Open Worlds", update_open_world_channel),
        ("Duviri and Zariman", update_duviri_channel),
        ("Void Fissures", update_fissures_channel),
    )
    results = await asyncio.gather(
        *(update(env) for _, update in updates),
        return_exceptions=True,
    )

    failures = []
    for (name, _), result in zip(updates, results):
        if isinstance(result, Exception):
            print(f"Failed to update {name}: {result}")
            failures.append(name)

    return failures


async def on_scheduled(event, env, ctx):
    """Runs automatically according to the schedule set in wrangler.toml."""
    await _update_all_channels(env)


async def on_fetch(request, env, ctx):
    """Allows manual execution by opening the Worker URL in a web browser."""
    failures = await _update_all_channels(env)
    if failures:
        return Response.new(
            f"Update failed for: {', '.join(failures)}. Check Worker logs."
        )
    return Response.new(
        "All Discord channels updated successfully!"
    )
