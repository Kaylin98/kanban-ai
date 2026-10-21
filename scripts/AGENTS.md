# Scripts

Start and stop scripts for the Docker container (`pm-app`). Run them from any directory.

- `start.sh` / `stop.sh`: Mac and Linux
- `start.ps1` / `stop.ps1`: PC (`powershell -ExecutionPolicy Bypass -File scripts\start.ps1`)

Start builds the image, replaces any running container, and runs it with `--env-file .env` on port 8000 and the named volume `pm-data` mounted at `/app/data` for the database. Stop removes the container (the volume is kept).
