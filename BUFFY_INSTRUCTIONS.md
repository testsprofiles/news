# BUFFY RULES FOR NEWS PORTAL PROJECT

- Efficiency: Do NOT scan the whole repository unnecessarily. Work strictly on requested files.
- Code Generation: Output changes as minimal diffs or clear isolated blocks.
- Auto Verification: After modifying any code, IMMEDIATELY run:
  1. `pytest` (or `pytest tests/`)
  2. Frontend typecheck (`npx tsc --noEmit`) if UI is modified.
- Auto Commit & Push: If tests pass with 0 errors, automatically run `git commit` with a descriptive message and execute `git push`.
- Git Commit Sign-off: Never add Co-Authored-By or AI signatures to git commit messages. Commit strictly as the repository owner.
- Architecture Safety: Maintain `db_cursor` contextmanager in `database.py`, JWT verification (`@token_required`), and Telegram bot notifications in `bot/notifier.py`.
- Human Clarification Triggers: STOP and ask for explicit confirmation ONLY if modifying DB schema/migrations, installing heavy packages, or changing `.env`.
