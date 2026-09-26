# ==========================================================
# WEB APPLICATION BACKEND
# Node.js + Express.js + Prisma
# ==========================================================

# ---- deps stage: install once, reused by build & production ------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# ---- build stage: generate the Prisma client -----------------------
FROM deps AS build
WORKDIR /app
COPY prisma ./prisma
RUN npx prisma generate
COPY . .

# ---- production stage ---------------------------------------------
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -S app && adduser -S app -G app

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
