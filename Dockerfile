FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OPENBB_BLS_CACHE_TTL=21600

WORKDIR /app
COPY . /app

RUN pip install . openbb-platform-api \
    && useradd --create-home --uid 10001 app \
    && chown -R app /app
USER app

EXPOSE 6969

CMD ["python", "start.py"]
