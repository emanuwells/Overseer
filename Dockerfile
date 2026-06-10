FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install -r requirements.txt && pip install --no-deps .

COPY . .

EXPOSE 8090

CMD ["uvicorn", "overseer_api.main:app", "--host", "0.0.0.0", "--port", "8090"]
