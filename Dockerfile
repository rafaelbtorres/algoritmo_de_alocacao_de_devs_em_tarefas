FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY start.sh ./
COPY config ./config
COPY scripts ./scripts
COPY app ./app
COPY tests ./tests
COPY web ./web
CMD ["sleep", "infinity"]
