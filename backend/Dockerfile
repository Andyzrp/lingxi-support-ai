FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt /app/requirements.txt

# 安装Python依赖（使用国内镜像加速）
# 注意：requirements.txt 中的 pywin32 仅 Windows 平台需要，Linux 容器中安装会失败，这里跳过
RUN grep -v '^pywin32' requirements.txt > /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --extra-index-url https://download.pytorch.org/whl/cpu

# 复制代码
COPY . /app

# 暴露端口
EXPOSE 8000

# 启动命令（uvicorn 启动 FastAPI 应用）
# celery worker 共用本镜像，在 docker-compose.yml 中通过 command 覆盖启动指令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
