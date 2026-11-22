# Legal bot — public website image
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LEGALBOT_PUBLIC=1 HF_HOME=/app/.hf
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt
COPY . .
# ready-made index (notes + legislation + official judgments) and the two search models, baked into the image
RUN python -m legalbot.index fetch
# listen on all interfaces inside the container; the platform supplies $PORT
CMD ["sh", "-c", "python -m legalbot.run --host 0.0.0.0 --port ${PORT:-8800}"]
