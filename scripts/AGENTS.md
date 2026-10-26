# Scripts

Start and stop scripts for the Docker container (`pm-app`). Run them from any directory.

- `start.sh` / `stop.sh`: Mac and Linux
- `start.ps1` / `stop.ps1`: PC (`powershell -ExecutionPolicy Bypass -File scripts\start.ps1`)
- `hash_password.py`: prompts for a password and prints the argon2 hash for `APP_PASSWORD_HASH` (`uv run scripts/hash_password.py`; uv installs its one dependency)

Start builds the image, replaces any running container, and runs it with `--env-file .env` on port 8000, the named volume `pm-data` mounted at `/app/data` for the database, and `certs/` mounted read-only at `/app/certs`. Stop removes the container (the volume is kept). The app refuses to start unless `.env` sets `APP_USERNAME`, `APP_PASSWORD_HASH` and `SESSION_SECRET` (see `.env.example`); check `docker logs pm-app` if the page doesn't load.

If `NODE_EXTRA_CA_CERTS` points to a file (Norton sets it to its HTTPS scanning root), start copies it to `certs/extra-ca.pem` (gitignored). The container adds any `/app/certs/*.pem` to its CA bundle at startup. Without it, the container uses the system CAs only. Certs are never built into the image.
