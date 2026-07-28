from duviri import update_duviri_channel
from js import Response
from open_world import update_open_world_channel


async def on_scheduled(event, env, ctx):
    """Runs automatically according to the schedule set in wrangler.toml."""
    await update_open_world_channel(env)
    await update_duviri_channel(env)


async def on_fetch(request, env, ctx):
    """Allows manual execution by opening the Worker URL in a web browser."""
    await update_open_world_channel(env)
    await update_duviri_channel(env)
    return Response.new(
        "All Discord channels updated successfully!"
    )