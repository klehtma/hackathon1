FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app


# ============================================================
# System dependencies
# ============================================================

FROM base AS system

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        libgtk-3-0 \
        libdbus-glib-1-2 \
        libasound2 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxshmfence1 \
        libpango-1.0-0 \
        libcairo2 \
        fonts-liberation \
        fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# Python dependencies
# ============================================================

FROM system AS dependencies

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# ============================================================
# Production
# ============================================================

FROM dependencies AS production

RUN groupadd --system app \
    && useradd --system \
        --gid app \
        --create-home \
        --home-dir /home/app \
        app

COPY --chown=app:app . .

USER app

CMD ["python", "main.py"]