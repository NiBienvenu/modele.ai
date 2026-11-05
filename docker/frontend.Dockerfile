# ==========================================================================
# Frontend image: build the React app, then serve it with nginx.
# nginx also forwards /question and /response to the backend, so the
# browser talks to a single address (no CORS needed).
# ==========================================================================

# ---- 1. Build ----
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2. Serve ----
FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
