FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY start.sh ./
COPY config ./config
COPY app ./app
COPY docs/Bmatching_LICENSE.txt ./docs/Bmatching_LICENSE.txt
COPY web ./web
CMD ["sleep", "infinity"]
