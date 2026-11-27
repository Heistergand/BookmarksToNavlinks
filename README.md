# BookmarksToNavlinks

An Ingress IITC Bookmarks Navigation Helper Telegram Bot.

## Installation

Requirements: Docker and Docker Compose v2.

1. Clone this repository and enter its directory.
2. Create a Telegram bot using [@BotFather](https://t.me/BotFather)
   or use an existing bot.
3. Create the local configuration as a non-root user:

   ```sh
   umask 077
   cp -n .secrets-template .secrets
   chmod 600 .secrets
   printf 'PUID=%s\nPGID=%s\n' "$(id -u)" "$(id -g)" > .env
   ```

4. Edit `.secrets` and enter your bot token and Telegram user ID.
5. Build and start the container:

   ```sh
   docker compose build --pull --no-cache
   docker compose up -d
   ```

## Updates

```sh
git pull --ff-only
docker compose build --pull --no-cache
docker compose up -d
```

## Security

- Supported Python 3.13 base image.
- Debian package updates during image builds.
- Non-root container execution.
- Read-only container filesystem.
- All Linux capabilities dropped.
- Privilege escalation disabled.
- Restricted Docker build context.
- Read-only secrets mount.
- No published network ports.
- Docker log rotation enabled.

Never commit `.secrets` or `.env` to version control.

## Vulnerability scanning

The container image can be scanned using Trivy:

```sh
trivy image --scanners vuln,secret bookmarkstonavlinks-bot:latest
```

See [SECURITY.md](SECURITY.md) for known security findings.
