FROM node:24-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /bin/uv

WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/backend/.venv/bin:$PATH"

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Trust the system CAs plus any extra CA certs in certs/ (Norton's, copied there by scripts/start).
COPY certs/ /app/certs/
RUN { cat /etc/ssl/certs/ca-certificates.crt; find /app/certs -name '*.pem' -exec cat {} +; } > /app/ca-bundle.pem
ENV SSL_CERT_FILE=/app/ca-bundle.pem

COPY backend/ ./
COPY --from=frontend /app/frontend/out /app/frontend/out

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
