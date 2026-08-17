# Contributing to Nexus ADV Bot

Thanks for helping improve Nexus ADV Bot.

## Development setup

1. Fork and clone the repository.
2. Create a virtual environment with Python 3.11 or newer.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and `config.example.json` to `config.json`.
5. Use a test Discord server and a dedicated development bot token.

Never commit `.env`, `config.json`, bot tokens, private server IDs, or user data.

## Before opening a pull request

```bash
python -m compileall -q main.py cogs utils
```

Test changed commands in a private server, including permission failures and invalid input. Keep pull requests focused, explain any configuration changes, and update the README when user-facing behavior changes.

## Reporting bugs

Include the command, expected result, actual result, Python version, and relevant traceback. Remove bot tokens, server IDs, channel IDs, and user data before posting logs.
