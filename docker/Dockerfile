FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY src/requirements.txt src/pyproject.toml ./src/
COPY src/overseer_api ./src/overseer_api
COPY src/overseer_core ./src/overseer_core
COPY src/overseer_agent ./src/overseer_agent
COPY src/overseer_sdk ./src/overseer_sdk
COPY src/overseer_monitor ./src/overseer_monitor
RUN pip install -r src/requirements.txt && pip install --no-deps ./src

COPY --from=frontend-build /app/frontend/dist ./frontend/dist
COPY deploy/runners ./deploy/runners
COPY scripts ./scripts
COPY openapi ./openapi

EXPOSE 8090

CMD ["uvicorn", "overseer_api.main:app", "--host", "0.0.0.0", "--port", "8090"]
