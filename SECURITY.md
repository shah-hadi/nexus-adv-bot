# Security policy

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository. Do not open a public issue containing an exploit, bot token, private server identifier, or user data.

Include a concise description, reproduction steps, impact, and any suggested mitigation. You should receive an initial response within seven days.

## Supported version

Security fixes target the latest commit on the `main` branch.

## Operational guidance

- Keep the Discord bot token only in `.env` or a secret manager.
- Grant the bot only the permissions required by its enabled commands.
- Restrict sensitive commands through `config.json` role rules.
- Rotate the bot token immediately if it is exposed.
- Review command logs without publishing private server or member data.
