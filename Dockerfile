# 允许通过 BASE_IMAGE 切换 CPU/GPU 镜像
# CPU 示例：paddlepaddle/paddle:3.2.0
# GPU 示例：paddlepaddle/paddle:3.2.0-gpu-cuda11.8-cudnn8
ARG BASE_IMAGE=paddlepaddle/paddle:3.2.0
FROM ${BASE_IMAGE}

# 设置工作目录
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PADDLE_PDX_CACHE_HOME=/opt/paddle-cache

# 预先安装依赖（基础镜像已含 Paddle，本处安装 OCR/框架依赖）
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# 拷贝服务代码与静态页
COPY server.py .
COPY static ./static

# 暴露端口
EXPOSE 8000

# 容器启动命令：Uvicorn 起 FastAPI
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
