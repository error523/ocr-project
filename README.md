# Paddle OCR 服务（CPU/GPU）

基于 **PaddleOCR** + **FastAPI** 的轻量 OCR 服务，支持 CPU 或 GPU 运行，提供图片/PDF 文字识别接口，并内置简单前端页用于快速验证。

## 快速开始（Docker 推荐）
1. 构建镜像（默认 CPU 基础镜像，可切 GPU 镜像）：
   ```bash
   # CPU（默认）
   docker build -t paddle-ocr-cpu .

   # GPU（示例：CUDA 11.8）
   docker build --build-arg BASE_IMAGE=paddlepaddle/paddle:3.2.0-gpu-cuda11.8-cudnn8 -t paddle-ocr-gpu .
   ```
2. 运行容器（挂载模型缓存目录，避免重复下载）：
   ```bash
   # CPU 运行
   docker run --rm -p 8000:8000 \
     -v $(pwd)/paddle-cache:/opt/paddle-cache \
     paddle-ocr-cpu

   # GPU 运行（需正确挂载 GPU 设备，例如 --gpus all）
   docker run --rm --gpus all -e USE_GPU=true -p 8000:8000 \
     -v $(pwd)/paddle-cache:/opt/paddle-cache \
     paddle-ocr-gpu
   ```
3. 调用示例：
   ```bash
   curl -X POST \
     -F "file=@/path/to/your/file.pdf" \
     http://localhost:8000/ocr
  ```

接口：
- `POST /ocr` 上传单个文件（图片或 PDF），返回分页面的文字/置信度/检测框
- `GET /health` 健康检查
- `GET /` 前端验证页，可上传文件并查看返回 JSON

> 首次运行会下载 OCR 模型，需联网。下载完成后同目录会缓存，后续启动更快。

## 本地开发
1. 安装 Paddle（CPU 或 GPU 版，按需选镜像源）：
   ```bash
   # CPU
   pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/whl/cpu

   # GPU 示例：CUDA 11.8
   pip install paddlepaddle-gpu==3.2.0.post118 -i https://www.paddlepaddle.org.cn/whl/cu118
   ```
2. 安装其余依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动开发服务器：
   ```bash
   uvicorn server:app --reload --port 8000
   ```

## 目录结构
```
.
├── Dockerfile       # 生产运行镜像（可切 CPU/GPU）
├── README.md        # 说明文档
├── requirements.txt # 依赖列表
├── server.py        # FastAPI 服务入口
└── static/          # 简单前端验证页
```

## 后续可做
- 增加批量 OCR、版面分析、表格/公式识别等接口
- 补充调用日志、简单鉴权和限流
- 添加接口级别测试和模型缓存预热
