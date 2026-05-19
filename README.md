# linkedin-cli

[![Latest Release](https://img.shields.io/github/v/release/DanielVd/linkedin-cli)](https://github.com/DanielVd/linkedin-cli/releases/latest)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-unlicensed-lightgrey)

CLI for LinkedIn Consumer APIs: OAuth login, profile lookup, posting, media upload, queue scheduler, and diagnostics.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Diagnostics](#diagnostics)
- [Runtime Files](#runtime-files)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

## Features

- OAuth login flows (`login`, `auth-url`, `exchange-token`)
- Profile commands (`me`, `whoami`)
- Post publishing (`post-text`, `post-link`, `post-file`, `post-image`, `post-carousel`)
- Queue scheduling (`queue-add`, `queue-list`, `queue-run`)
- Diagnostics (`doctor`, `oauth-debug`)

## Requirements

- Python 3.10+
- LinkedIn Developer app and valid scopes

## Installation

```bash
git clone https://github.com/DanielVd/linkedin-cli.git
cd linkedin-cli
python3 -m venv .venv
. .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name linkedin-cli linkedin_cli.py
```

## Quick Start

```bash
linkedin-cli init-config --client-id "..." --client-secret "..." --redirect-uri "http://localhost:8080/callback" --scopes "openid,profile,w_member_social"
linkedin-cli login
linkedin-cli whoami
```

## Commands

```bash
linkedin-cli --help
```

## Diagnostics

```bash
linkedin-cli doctor
linkedin-cli oauth-debug --code "..."
```

## Runtime Files

- `~/.config/linkedin-cli/config.json`
- `~/.config/linkedin-cli/queue.json`

## Troubleshooting

- OAuth callback error: verify redirect URI in app config
- Permission errors: verify requested scopes
- Post failures: verify visibility and media permissions

## Security Notes

- Keep client secret outside shell history
- Do not commit OAuth credentials
