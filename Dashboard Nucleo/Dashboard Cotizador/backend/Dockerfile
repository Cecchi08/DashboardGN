FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY scripts ./scripts
COPY src/data ./src/data
COPY data/input ./data/input
RUN npm run build:data

FROM node:22-alpine AS runtime
ENV NODE_ENV=production PORT=1234 HOST=0.0.0.0
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY backend ./backend
COPY --from=build /app/dist/catalog.json ./dist/catalog.json
COPY --from=build /app/data/input ./data/input
EXPOSE 1234
USER node
CMD ["npm", "run", "start"]
