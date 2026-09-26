# ==========================================================
# FRONTEND
# React + Vite, built to static assets and served by Nginx
# ==========================================================

# ---- build stage -------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# Install deps first for better layer caching
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .

# Backend URL to bake into the static build. Left empty (relative) by
# default because nginx.conf proxies /api/* to the backend container —
# only override this if the backend is hosted on a different origin.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# ---- production stage --------------------------------------------
FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=10s \
  CMD wget -qO- http://127.0.0.1:80/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
