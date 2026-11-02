# Warframe Cycles & Status Discord Bot (Cloudflare Workers + Python)

> ⚠️ **Work in Progress**: This project is under active development. Features may change.

This project uses [Cloudflare Workers](https://workers.cloudflare.com/) and Python to automatically update Discord messages with real-time Warframe status information. It fetches data from the [Warframe Worldstate API](https://api.warframestat.us/) and runs on a schedule using free [Cron Triggers](https://developers.cloudflare.com/workers/platform/triggers/cron-triggers/).

## Features

- **Open Worlds**: Displays the day/night and warm/cold cycles for Cetus, Orb Vallis, and Cambion Drift.
- **Duviri & Zariman**: Tracks the current Duviri spiral and Zariman bounties.
- **Baro Ki'Teer**: Shows his arrival status and location, and updates a separate Discord message with his inventory when he arrives or leaves.

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

### 2. Cloudflare Worker Variables and Secrets

In each Cloudflare Worker's dashboard, go to *Settings > Variables* and configure the required bindings:

| Variable | Description |
| :--- | :--- |
| `DISCORD_TOKEN` | Discord bot token. Set this on both Workers. |
| `OPEN_WORLD_CHANNEL_ID` | Channel ID for the Open Worlds status message (cycles Worker). |
| `OPEN_WORLD_MESSAGE_ID` | Message ID for the Open Worlds status message (cycles Worker). |
| `DUVIRI_CHANNEL_ID` | Channel ID for the Duviri & Zariman status message (cycles Worker). |
| `DUVIRI_MESSAGE_ID` | Message ID for the Duviri & Zariman status message (cycles Worker). |
| `DISCORD_CHANNEL` | Channel containing the Baro messages (Baro Worker). |
| `BARO_MSG1_ID` | Baro status and countdown message ID (Baro Worker). |
| `BARO_MSG2_ID` | Baro inventory message ID (Baro Worker). |
| `GITHUB_TOKEN` | Token authorized to dispatch a repository event (Baro Worker). |
| `GITHUB_REPO` | Repository in `owner/repository` format (Baro Worker). |

Add these GitHub Actions repository secrets under *Settings > Secrets and variables > Actions*:

| Secret | Used by |
| :--- | :--- |
| `CLOUDFLARE_API_TOKEN` | Both deployment workflows. |
| `CLOUDFLARE_ACCOUNT_ID` | Both deployment workflows. |
| `DISCORD_TOKEN` | Baro inventory workflow. |
| `DISCORD_CHANNEL` | Baro inventory workflow; channel containing the inventory message. |
| `BARO_MSG2_ID` | Baro inventory workflow; inventory message ID. |

The Baro Worker checks Baro's state hourly. When his presence changes (or on its first check), it dispatches an event that runs the inventory workflow.

To update the inventory manually, open **Actions > Update Baro Inventory > Run workflow** and choose whether Baro is currently present. The workflow installs `requests` from [`scripts/requirements.txt`](scripts/requirements.txt) and updates the inventory message, or marks the shop closed when Baro is absent.

## 🚀 Deployment

1.  **Fork** this repository to your own GitHub account.
2.  Add the Cloudflare API token and account ID as GitHub Actions secrets, as described above.
3.  Configure the Workers' variables and secrets in Cloudflare.

The GitHub Actions workflows deploy the cycles Worker when files under `src/` or its Wrangler configuration change, and the Baro Worker when files under `baro-worker/` change. Their schedules are configured in the respective `wrangler.toml` files. Both Workers update on their configured Cloudflare Cron Triggers.

## Project Structure

```
.
├── baro-worker/
│   ├── src/main.py       # Baro status Worker; dispatches the inventory workflow when Baro's state changes.
│   └── wrangler.toml     # Baro Worker configuration and hourly schedule.
├── scripts/
│   ├── fetch_baro_inventory.py  # Fetches and formats Baro's inventory for Discord.
│   └── requirements.txt         # Python dependencies for the inventory workflow.
├── src/
│   ├── duviri.py       # Fetches Duviri and Zariman cycle data and updates Discord.
│   ├── entry.py        # Cycles Worker entry point.
│   ├── open_world.py   # Fetches open-world cycle data and updates Discord.
│   └── utils.py        # Shared API, time-formatting, and Discord helpers.
├── .github/
│   ├── workflows/      # Worker deployment and Baro inventory workflows.
│   └── dependabot.yml  # Weekly dependency update checks for pip and GitHub Actions.
├── README.md
└── wrangler.toml       # Cycles Worker configuration and schedule.
```