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

COPY backend/ ./
COPY --from=frontend /app/frontend/out /app/frontend/out

# Trust the system CAs plus any extra CA certs mounted at /app/certs at runtime (Norton's,
# mounted by scripts/start). Certs are never built into the image.
ENV SSL_CERT_FILE=/tmp/ca-bundle.pem
# Render sets PORT; locally it defaults to 8000.
EXPOSE 8000
CMD ["sh", "-c", "cat /etc/ssl/certs/ca-certificates.crt /app/certs/*.pem > /tmp/ca-bundle.pem 2>/dev/null; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
