# ==========================================
# STAGE 1: React Frontend Compiler
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend source files
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Python Backend & Runner
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY backend/ ./

# Copy compiled React static assets from Stage 1 into backend serving folder
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose standard Cloud Run target port (Cloud Run sets $PORT environment variable, default 8080)
EXPOSE 8080

# Run FastAPI uvicorn server serving on all interfaces
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
