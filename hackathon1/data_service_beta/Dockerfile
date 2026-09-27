FROM python:3.13-slim

# Runtime libraries Camoufox's bundled Firefox needs to actually launch.
# This list comes from working examples elsewhere; if the container still
# fails with a "cannot open shared object file" error on startup, the
# missing library name will be right there in the error — just add it here.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libx11-xcb1 \
    libasound2 \
    libglib2.0-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Downloads the actual browser binary + fingerprint/geoip data at build
# time, so the container doesn't need to fetch it (and doesn't fail) on
# every start.
RUN camoufox fetch

COPY . .

CMD ["python", "main.py"]
