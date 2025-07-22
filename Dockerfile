FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    aiohttp aioredis websockets numpy pandas ta tensorflow-cpu torch torch-geometric \
    stable-baselines3 transformers asyncpraw feedparser cryptography pytest psutil
CMD ["python", "-m", "utils.orchestrator_zero_gap"]