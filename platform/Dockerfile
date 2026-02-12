# Stage 1: Build React Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend

# Copy frontend dependency files
COPY package*.json ./
# Install dependencies
RUN npm ci

# Copy frontend source code
COPY . .
# Build the React app (output usually in dist/)
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.11-slim as backend-build
WORKDIR /app/backend

# Install system dependencies for potential python packages (e.g. gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copcy backend code
COPY backend/ .

# Stage 3: Final Image
FROM python:3.11-slim
WORKDIR /app

# Copy built frontend assets
COPY --from=frontend-build /app/frontend/dist /app/static

# Copy installed python packages from backend-build
COPY --from=backend-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /usr/local/bin /usr/local/bin

# Copy backend code
COPY --from=backend-build /app/backend /app

# Expose port (Cloud Run defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Run the application
# We assume main.py is in /app and has been updated to serve static files from /app/static
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]