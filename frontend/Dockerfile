# Frontend Development Dockerfile
FROM node:18-alpine

WORKDIR /app

# 1. Install dependencies first (caching)
COPY package*.json ./
RUN npm install

# 2. Copy source code
COPY . .

# 3. Expose Vite port (matches vite.config.js)
EXPOSE 3000

# 4. Run Vite with --host so it's accessible outside container
CMD ["npm", "run", "dev", "--", "--host"]
