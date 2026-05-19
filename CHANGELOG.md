# Changelog

All notable changes to this project are documented in this file.

## [0.1.1] - 2026-05-19

### Changed

- Enforced English-only user-facing runtime output across all CLI commands.
- Improved README structure and added Contributing/Changelog references.

### Fixed

- Removed remaining non-English runtime strings in posting and profile steps.
- Hardened CI English-only guard reliability.

### CI

- Installed `ripgrep` in GitHub Actions before English-only checks.
- Updated GitHub Actions versions (`actions/checkout@v5`, `actions/setup-python@v6`).

## [0.1.0] - 2026-05-19

### Added

- LinkedIn OAuth 2.0 CLI flow with browser callback.
- Profile commands: `me`, `whoami`.
- Publishing commands: `post-text`, `post-link`, `post-file`, `post-image`, `post-carousel`.
- Queue commands: `queue-add`, `queue-list`, `queue-run`.
- Diagnostics commands: `doctor`, `oauth-debug`.
- Single-file executable build via PyInstaller.
- CI workflow with English-only guard, compile check, build, and smoke test.

### Changed

- Default login/auth flow set to non-PKCE for compatibility with current LinkedIn app setup.
- Full English-only user-facing output and docs.

### Fixed

- Multiple residual non-English runtime messages.
- CI guard reliability (`ripgrep` installation and self-match exclusion).
