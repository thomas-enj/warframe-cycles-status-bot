# Warframe Cycles & Status Discord Bot (Cloudflare Workers + Python)

> ⚠️ **Work in Progress**: This project is under active development. Features may change.

This project uses [Cloudflare Workers](https://workers.cloudflare.com/) and Python to automatically update Discord messages with real-time Warframe status information. It fetches data from the [Warframe Worldstate API](https://api.warframestat.us/) and runs on a schedule using free [Cron Triggers](https://developers.cloudflare.com/workers/platform/triggers/cron-triggers/).

## Features

- **Open Worlds**: Displays the day/night and warm/cold cycles for Cetus, Orb Vallis, and Cambion Drift.
- **Duviri & Zariman**: Tracks the current Duviri spiral and Zariman bounties.
- **Extensible**: Designed to easily add more trackers, like Baro Ki'Teer's arrival.

## Prerequisites

1.  A [Cloudflare](https://dash.cloudflare.com/sign-up) account.
2.  A [GitHub](https://github.com/) account.
3.  A Discord application and bot token from the [Discord Developer Portal](https://discord.com/developers/applications).

## ⚙️ Configuration

### 1. Discord Bot Setup

- Invite your bot to your Discord server with `View Channel` and `Send Messages` permissions.
- Enable **Developer Mode** in Discord (*Settings > Advanced*) to copy IDs.
- In the channels you want the bot to post in, send placeholder messages (e.g., "Loading...").
- Right-click on the channel and the message to copy the **Channel ID** and **Message ID** for each status panel.

### 2. Cloudflare Worker Secrets

In your Cloudflare Worker's dashboard, go to *Settings > Variables* and add the following secrets under **Environment Variable Bindings**:

| Variable | Description |
| :--- | :--- |
| `DISCORD_TOKEN` | Your Discord bot token. |
| `OPEN_WORLD_CHANNEL_ID` | The Channel ID for the Open Worlds status message. |
| `OPEN_WORLD_MESSAGE_ID` | The Message ID for the Open Worlds status message. |
| `DUVIRI_CHANNEL_ID` | The Channel ID for the Duviri & Zariman status message. |
| `DUVIRI_MESSAGE_ID` | The Message ID for the Duviri & Zariman status message. |

## 🚀 Deployment

1.  **Fork** this repository to your own GitHub account.
2.  In the Cloudflare dashboard, create a new Worker.
3.  Connect your Worker to your GitHub fork (*Settings > Deployments*). Enable automatic deployments on the `main` branch.
4.  Go to the *Triggers* tab in your Worker's settings and add a **Cron Trigger** to run the script on a schedule (e.g., `*/5 * * * *` to run every 5 minutes).

Your bot will now deploy and update automatically on every `git push` to the main branch.

## Project Structure

```
.
├── src/
│   ├── duviri.py       # Logic for fetching Duviri and Zariman cycle data and updating Discord.
│   ├── entry.py        # Main entry point for the Cloudflare Worker, handling triggers and coordinating updates.
│   ├── open_world.py   # Logic for fetching Cetus, Orb Vallis, Cambion Drift cycle data and updating Discord.
│   └── utils.py        # Utility functions for API interaction, time formatting, and Discord message sending.
├── .gitignore          # Specifies intentionally untracked files to ignore.
├── README.md           # Project README file.
├── wrangler.toml       # Configuration file for Cloudflare Workers.
└── .wrangler/          # Local development assets and build artifacts for Cloudflare Workers.
```