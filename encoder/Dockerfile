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

# 安装 torch（大包独立成层,失败重试时不再重复下载）
RUN pip install --no-cache-dir torch==2.3.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# 安装其余 Python 依赖（torch 已装好会被跳过；使用国内镜像加速）
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://download.pytorch.org/whl/cpu

# 使用 HuggingFace 国内镜像下载模型（huggingface.co 直连在境内不可用）
ENV HF_ENDPOINT=https://hf-mirror.com

# 预下载模型（构建时缓存，避免启动时下载）
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('BAAI/bge-small-zh-v1.5')"

# 复制代码
COPY . /app

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]