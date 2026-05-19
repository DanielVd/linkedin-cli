# linkedin-cli

CLI LinkedIn Consumer API stile gogcli.

## Cosa fa

- OAuth2 LinkedIn con comando `login` automatico (browser + callback localhost)
- Modalità manuale (`auth-url` + `exchange-token`)
- Lettura profilo (`me`, `whoami`)
- Pubblicazione post (`post-text`, `post-link`, `post-file`, `post-image`, `post-carousel`)
- Queue scheduler locale (`queue-add`, `queue-list`, `queue-run`)
- Diagnostica (`doctor`, `oauth-debug`)

## Requisiti

- Python 3.10+
- App LinkedIn configurata in LinkedIn Developer Portal
- Redirect URI HTTP locale, esempio: `http://localhost:8080/callback`

## Setup

```bash
./dist/linkedin-cli init-config \
  --client-id "LINKEDIN_CLIENT_ID" \
  --client-secret "LINKEDIN_CLIENT_SECRET" \
  --redirect-uri "http://localhost:8080/callback" \
  --scopes "openid,profile,w_member_social"
```

## Login

Default: **no-PKCE** (compatibile col tuo scenario n8n)

```bash
./dist/linkedin-cli login
```

Per abilitare PKCE:

```bash
./dist/linkedin-cli login --pkce
```

## API

```bash
./dist/linkedin-cli whoami
./dist/linkedin-cli me

./dist/linkedin-cli post-text --text "Ciao LinkedIn da CLI" --visibility PUBLIC
./dist/linkedin-cli post-link --text "Leggi" --url "https://example.com" --visibility PUBLIC
./dist/linkedin-cli post-file --path ./post.txt --visibility PUBLIC
./dist/linkedin-cli post-image --path ./img.png --text "Foto" --visibility PUBLIC
./dist/linkedin-cli post-carousel --paths ./1.png ./2.png --text "Carousel" --visibility PUBLIC
```

## Queue

```bash
./dist/linkedin-cli queue-add --type post_text --run-at "2026-05-19T08:30:00+00:00" --payload ./payload.json
./dist/linkedin-cli queue-list
./dist/linkedin-cli queue-run
./dist/linkedin-cli queue-run --force
```

## Diagnostica

```bash
./dist/linkedin-cli doctor
./dist/linkedin-cli oauth-debug --code "..."
```

## File runtime

- Config: `~/.config/linkedin-cli/config.json`
- Queue: `~/.config/linkedin-cli/queue.json`
- Log: `~/.config/linkedin-cli/linkedin-cli.log`

## Nota importante

LinkedIn limita scope/endpoint in base al prodotto abilitato su app.
Se un comando post fallisce con `403`, mancano permessi/scope/prodotto corretti.
