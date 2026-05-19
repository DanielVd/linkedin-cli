# linkedin-cli

A command-line client for LinkedIn Consumer APIs, inspired by `gogcli`.

## Features

- OAuth 2.0 login (browser + localhost callback)
- Manual OAuth flow (`auth-url`, `exchange-token`)
- Profile endpoints (`me`, `whoami`)
- Publishing commands:
  - `post-text`
  - `post-link`
  - `post-file`
  - `post-image`
  - `post-carousel`
- Local queue/scheduler:
  - `queue-add`
  - `queue-list`
  - `queue-run`
- Diagnostics:
  - `doctor`
  - `oauth-debug`

## Requirements

- Linux/macOS environment
- Python 3.10+ (only required to build from source)
- LinkedIn Developer app with required products/scopes
- Redirect URI configured in LinkedIn app (example: `http://localhost:8080/callback`)

## Install

### Prebuilt binary (local build output)

```bash
./dist/linkedin-cli --help
```

### Build binary from source

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name linkedin-cli linkedin_cli.py
./dist/linkedin-cli --help
```

## Quick Start

1) Configure app credentials:

```bash
./dist/linkedin-cli init-config \
  --client-id "LINKEDIN_CLIENT_ID" \
  --client-secret "LINKEDIN_CLIENT_SECRET" \
  --redirect-uri "http://localhost:8080/callback" \
  --scopes "openid,profile,w_member_social"
```

2) Login (default: no PKCE):

```bash
./dist/linkedin-cli login
```

3) Validate identity:

```bash
./dist/linkedin-cli whoami
```

4) Publish a test post:

```bash
./dist/linkedin-cli post-text --text "Hello from linkedin-cli" --visibility CONNECTIONS
```

## Command Overview

```bash
./dist/linkedin-cli --help
```

Key commands:

- `init-config`: Save OAuth app credentials.
- `show-config`: Print redacted local config.
- `login`: Start browser OAuth flow and store token.
- `auth-url`: Generate manual authorization URL.
- `exchange-token`: Exchange `code` for access token.
- `whoami` / `me`: Read profile info.
- `post-*`: Publish content.
- `queue-*`: Queue and run scheduled jobs.
- `doctor`: Local environment diagnostics.
- `oauth-debug`: Token exchange debugging.

## Runtime Files

- Config: `~/.config/linkedin-cli/config.json`
- Queue: `~/.config/linkedin-cli/queue.json`
- Log: `~/.config/linkedin-cli/linkedin-cli.log`

## Troubleshooting

- `redirect_uri does not match`: ensure exact URI match between CLI config and LinkedIn app settings.
- `invalid_client`: verify `client_id` + active `client_secret` for the exact same LinkedIn app.
- `403` on publish: required product/scope not enabled for app.

## Security Notes

- Do not commit real client secrets.
- Rotate secrets after sharing credentials.
- Prefer token-based git auth over password in remote URLs.

## License

No license file added yet.
