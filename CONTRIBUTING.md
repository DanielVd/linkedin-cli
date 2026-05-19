# Contributing

Thanks for contributing to `linkedin-cli`.

## Development Setup

```bash
git clone https://github.com/DanielVd/linkedin-cli.git
cd linkedin-cli
python3 -m venv .venv
. .venv/bin/activate
pip install pyinstaller
```

## Local Checks

Run before opening a PR:

```bash
python -m py_compile linkedin_cli.py
pyinstaller --onefile --name linkedin-cli linkedin_cli.py
./dist/linkedin-cli --help
```

## English-only Rule

All user-facing CLI output, docs, comments, and help text must be in English.

## Commit Style

Use concise Conventional Commit style when possible:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `ci: ...`
- `chore: ...`

## Pull Requests

Please include:

- clear summary
- test steps and command output
- any breaking change notes
