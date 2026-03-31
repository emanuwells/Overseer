# Secrets Folder Policy

This folder stores local production credentials only.

## Required local files (not for git)
- `database.json`
- `slack.json`
- optional SSH keys

## Tracked files allowed
- `*.example`
- `*.example.json`
- `.gitkeep`
- this `README.md`

## Security rules
- Never commit real credentials.
- Use chmod 600 for secret files in Linux.
- Rotate credentials immediately if leaked.
