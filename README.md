<div align="center">

![Kyro — Discord Operations, Engineered](assets/kyro-hero.png)

# Kyro

**Discord operations, engineered for clarity and control.**

[![CI](https://github.com/shah-hadi/kyro/actions/workflows/ci.yml/badge.svg)](https://github.com/shah-hadi/kyro/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.4%2B-5865F2?logo=discord&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)

An advanced Discord operations bot with interactive configuration, granular access control, polished command interfaces, and dependable moderation workflows.

</div>

## Why Kyro

Kyro brings moderation, server configuration, role-based access, voice operations, and audit visibility into one coherent command system. It supports both slash and prefix workflows without forcing administrators to edit source code for routine server changes.

## Highlights

- Hybrid prefix and slash commands
- Interactive per-server configuration panel
- Per-server prefixes, audit channels, admin roles, and command permissions
- Kick, ban, timeout, unban, and purge workflows
- Channel locking, visibility, and slowmode controls
- Voice move, disconnect, mute, deafen, and user-limit tools
- Temporary roles with automatic expiry and recovery
- Configurable role-based command permissions
- Interactive command help menu
- Branded command responses backed by a dedicated emoji system
- Target-aware command and configuration audit logs
- Flexible user, member, role, and channel converters

## Capability map

| Area | What Kyro handles |
| --- | --- |
| **Configuration** | Interactive per-server setup for prefixes, audit channels, admin roles, and command permissions |
| **Moderation** | Kick, ban, unban, timeout, cleanup, and structured action logging |
| **Channels & roles** | Locking, visibility, slowmode, nicknames, permanent roles, and expiring temporary roles |
| **Voice operations** | Member movement, bulk moves, disconnects, mute/deafen controls, location, and limits |
| **Utilities** | Profile and server information, avatar/banner lookup, emoji and sticker importing |
| **Experience** | Hybrid commands, branded embeds, interactive help, focused errors, and custom emoji theming |

## Tech stack

- Python 3.11+
- discord.py 2.4+
- python-dotenv

## Local setup

```bash
git clone https://github.com/shah-hadi/kyro.git
cd kyro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp config.example.json config.json
python main.py
```

Set your Discord bot token and owner ID in `.env`, then replace the placeholder server IDs in `config.json`.

## Configuration

`config.json` stores the default prefix, owner-managed no-prefix users, and per-server settings. Server administrators can manage the prefix, audit channel, bot-admin role, and command-level role access from Kyro's interactive `/config` panel. The real configuration is ignored by Git; use `config.example.json` as the starting point.

The bot requires the **Message Content** and **Server Members** privileged intents in the Discord Developer Portal.

## How it fits together

```text
Discord event
    ↓
Hybrid command router
    ↓
Permission + configuration layer
    ↓
Focused command module
    ↓
Branded response + structured audit log
```

## Project structure

```text
cogs/                 Command modules
  channels.py         Text-channel and role tools
  general.py          Profiles, server info, media, and utilities
  help.py             Interactive command guide
  configuration.py    Interactive per-server configuration
  moderation.py       Member moderation commands
  voice.py            Voice-channel management
utils/                Permissions, converters, logging, and shared UI
theme.py              Optional bot artwork and emoji exporter
main.py               Bot startup and extension loading
```

## Security

Never commit `.env`, `config.json`, or a Discord bot token. If a token is exposed, reset it immediately in the Discord Developer Portal.

## Project documentation

- [Contributing guide](CONTRIBUTING.md) — local setup, validation, and pull-request expectations
- [Security policy](SECURITY.md) — private reporting and safe bot operation

## License

Released under the [MIT License](LICENSE).
