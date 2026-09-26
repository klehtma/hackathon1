# ==========================================================
# WEB APPLICATION BACKEND
# Node.js + Express.js + Prisma
#
# Debian-based "slim" images, not alpine: Prisma's engine binaries
# need OpenSSL, and detection against musl libc (alpine) is unreliable
# ("Could not parse schema engine response" / libssl warnings).
# ==========================================================

# ---- deps stage: install once, reused by build & production ------
FROM node:20-slim AS deps
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*
COPY package*.json ./
RUN npm ci

# ---- build stage: generate the Prisma client -----------------------
FROM deps AS build
WORKDIR /app
COPY prisma ./prisma
RUN npx prisma generate
COPY . .

# ---- production stage ---------------------------------------------
FROM node:20-slim AS production
WORKDIR /app
ENV NODE_ENV=production
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/node_modules/.prisma ./node_modules/.prisma
COPY package*.json ./
COPY prisma ./prisma
COPY src ./src
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh && chown -R app:app /app

USER app

EXPOSE 3000

ENTRYPOINT ["./entrypoint.sh"]