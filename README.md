# Nexus ADV Bot

[![CI](https://github.com/shah-hadi/nexus-adv-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/shah-hadi/nexus-adv-bot/actions/workflows/ci.yml)

A modular Discord administration bot built for fast moderation, voice-channel control, role management, and everyday server utilities.

## Highlights

- Hybrid prefix and slash commands
- Kick, ban, timeout, unban, and purge workflows
- Channel locking, visibility, and slowmode controls
- Voice move, disconnect, mute, deafen, and user-limit tools
- Temporary roles with automatic expiry and recovery
- Configurable role-based command permissions
- Interactive command help menu
- Centralized command logging and error handling
- Flexible user, member, role, and channel converters

## Tech stack

- Python 3.11+
- discord.py 2.4+
- python-dotenv

## Local setup

```bash
git clone https://github.com/shah-hadi/nexus-adv-bot.git
cd nexus-adv-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp config.example.json config.json
python main.py
```

Set your Discord bot token and owner ID in `.env`, then replace the placeholder server IDs in `config.json`.

## Configuration

`config.json` controls the command prefix, logging channel, administrator role, no-prefix users, and per-command role access. The real configuration is ignored by Git; use `config.example.json` as the starting point.

The bot requires the **Message Content** and **Server Members** privileged intents in the Discord Developer Portal.

## Project structure

```text
cogs/                 Command modules
  channels.py         Text-channel and role tools
  general.py          Profiles, server info, media, and utilities
  help.py             Interactive command guide
  moderation.py       Member moderation commands
  voice.py            Voice-channel management
utils/                Permissions, converters, logging, and shared UI
main.py               Bot startup and extension loading
```

## Security

Never commit `.env`, `config.json`, or a Discord bot token. If a token is exposed, reset it immediately in the Discord Developer Portal.

## Project documentation

- [Contributing guide](CONTRIBUTING.md) — local setup, validation, and pull-request expectations
- [Security policy](SECURITY.md) — private reporting and safe bot operation

## License

Released under the [MIT License](LICENSE).
