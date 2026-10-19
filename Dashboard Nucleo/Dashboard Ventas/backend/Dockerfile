FROM python:3.12-slim AS data-builder
WORKDIR /workspace
COPY backend/data-builder/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts/update/actualizar.py ./scripts/update/actualizar.py
COPY docs/data/input ./docs/data/input
RUN BUILD_STANDALONE=0 BUILD_DASHBOARD_HTML=0 python -u scripts/update/actualizar.py

FROM node:22-alpine AS dependencies
WORKDIR /app
COPY backend/package*.json ./
RUN npm ci --omit=dev

FROM node:22-alpine AS runtime
ENV NODE_ENV=production PORT=4321 HOST=0.0.0.0
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY backend/package.json ./package.json
COPY backend/src ./src
COPY --from=data-builder /workspace/data/processed/data_raw_v2.json ./data/processed/data_raw_v2.json
COPY --from=data-builder /workspace/data/processed/aging.json ./data/processed/aging.json
EXPOSE 4321
USER node
CMD ["npm", "start"]
