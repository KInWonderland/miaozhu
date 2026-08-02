FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/KInWonderland/miaozhu"

WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

COPY . .
RUN mkdir -p data logs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
