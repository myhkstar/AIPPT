# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend dependency files
COPY frontend/package*.json ./
# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./
# Build frontend
RUN npm run build

# Stage 2: Backend
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration files from root
COPY pyproject.toml ./

# Install dependencies using a mirror for speed
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
    gunicorn \
    flask \
    flask-cors \
    google-genai \
    pydantic \
    pillow \
    python-pptx \
    python-dotenv \
    reportlab \
    werkzeug \
    markitdown \
    openai \
    firebase-admin \
    PyJWT

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend artifacts from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 1. 确保工作目录直接设在 backend 文件夹下
WORKDIR /app/backend

# 2. 再次确保依赖已安装（针对该目录）
# 如果你之前是在根目录安装的，请确保这步能找到 pyproject.toml 或 requirements.txt

# 3. 关键：将当前目录添加到 Python 路径，解决导入问题
ENV PYTHONPATH=/app/backend

# 4. 使用更直接的启动方式 (先用 python 启动确保能看到具体的报错)
# 4. 使用更直接的启动方式 (先用 python 启动确保能看到具体的报错)
CMD ["sh", "-c", "ls -R /app && python app.py"]

# 等 python app.py 能跑通后，再换回下面这行更专业的 Gunicorn 命令：
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]
