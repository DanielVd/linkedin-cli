# linkedin-cli

[![CI](https://github.com/DanielVd/linkedin-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/DanielVd/linkedin-cli/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-unlicensed-lightgrey)

A command-line client for LinkedIn Consumer APIs, inspired by `gogcli`.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Queue Jobs](#queue-jobs)
- [Diagnostics](#diagnostics)
- [Runtime Files](#runtime-files)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Changelog](#changelog)

## Features

- OAuth 2.0 login (browser + localhost callback)
- Manual OAuth flow (`auth-url`, `exchange-token`)
- Profile commands (`me`, `whoami`)
- Publishing commands:
  - `post-text`
  - `post-link`
  - `post-file`
  - `post-image`
  - `post-carousel`
- Local queue scheduler:
  - `queue-add`
  - `queue-list`
  - `queue-run`
- Diagnostics:
  - `doctor`
  - `oauth-debug`

## Requirements

- Linux or macOS
- Python 3.10+ (only for local build from source)
- LinkedIn Developer app with required products/scopes
- Redirect URI configured in LinkedIn app (example: `http://localhost:8080/callback`)

## Installation

### Option 1: System binary already installed

```bash
linkedin-cli --help
```

### Option 2: Build from source

```bash
git clone https://github.com/DanielVd/linkedin-cli.git
cd linkedin-cli
python3 -m venv .venv
. .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name linkedin-cli linkedin_cli.py
./dist/linkedin-cli --help
```

## Quick Start

1) Configure credentials:

```bash
linkedin-cli init-config \
  --client-id "LINKEDIN_CLIENT_ID" \
  --client-secret "LINKEDIN_CLIENT_SECRET" \
  --redirect-uri "http://localhost:8080/callback" \
  --scopes "openid,profile,w_member_social"
```

2) Login (default: no PKCE):

```bash
linkedin-cli login
```

3) Check identity:

```bash
linkedin-cli whoami
```

4) Publish test post:

```bash
linkedin-cli post-text --text "Hello from linkedin-cli" --visibility CONNECTIONS
```

## Commands

List all commands:

```bash
linkedin-cli --help
```

Main command groups:

- Auth/config: `init-config`, `show-config`, `login`, `auth-url`, `exchange-token`
- Profile: `whoami`, `me`
- Publishing: `post-text`, `post-link`, `post-file`, `post-image`, `post-carousel`
- Queue: `queue-add`, `queue-list`, `queue-run`
- Diagnostics: `doctor`, `oauth-debug`

## Queue Jobs

Add and execute scheduled jobs:

```bash
linkedin-cli queue-add --type post_text --run-at "2026-05-19T08:30:00+00:00" --payload ./payload.json
linkedin-cli queue-list
linkedin-cli queue-run
linkedin-cli queue-run --force
```

## Diagnostics

```bash
linkedin-cli doctor
linkedin-cli oauth-debug --code "..."
```

## Runtime Files

- Config: `~/.config/linkedin-cli/config.json`
- Queue: `~/.config/linkedin-cli/queue.json`
- Log: `~/.config/linkedin-cli/linkedin-cli.log`

## Troubleshooting

- `redirect_uri does not match`
  - Ensure exact URI match between CLI config and LinkedIn app settings.
- `invalid_client`
  - Verify `client_id` + active `client_secret` belong to the same app.
- `403` on publish commands
  - Required LinkedIn products/scopes are missing for the app.

## Security Notes

- Never commit real client secrets.
- Rotate secrets after accidental sharing.
- Prefer token/SSH auth for git remotes instead of passwords.

## Roadmap

- Add `queue-daemon` background runner.
- Add richer `whoami` output formatting options.
- Add optional JSON schema validation for queue payloads.

## Contributing

See `CONTRIBUTING.md`.

## Changelog

See `CHANGELOG.md`.
