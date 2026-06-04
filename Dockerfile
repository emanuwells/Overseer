FROM node:22-alpine AS webapp

WORKDIR /webapp
COPY webapp/package*.json ./
RUN npm ci
COPY webapp ./
RUN npm run build

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY --from=webapp /webapp/dist /app/webapp/dist

EXPOSE 8090

CMD ["uvicorn", "src.overseer_api.main:app", "--host", "0.0.0.0", "--port", "8090"]
