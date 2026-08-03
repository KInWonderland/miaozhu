# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/KInWonderland/miaozhu"

WORKDIR /app

ARG DEBIAN_MIRROR=mirrors.cloud.tencent.com
ARG PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple/
ARG PIP_TRUSTED_HOST=mirrors.cloud.tencent.com
ARG PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright

# 将 Debian 官方源替换为腾讯云镜像。生产 Compose 会传入腾讯云内网镜像域名。
RUN find /etc/apt -type f \( -name '*.list' -o -name '*.sources' \) \
    -exec sed -i "s|deb.debian.org|${DEBIAN_MIRROR}|g" {} +

# 系统包与业务依赖分层：仅修改应用代码时会直接复用这一层。
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get -o APT::Keep-Downloaded-Packages=true install -y --no-install-recommends \
    libreoffice \
    fonts-noto-cjk \
    fonts-wqy-zenhei

# BuildKit 会在服务器保留 pip 下载缓存；requirements.txt 未变化时，该层完全命中缓存。
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --prefer-binary --no-compile \
    --index-url "${PIP_INDEX_URL}" \
    --trusted-host "${PIP_TRUSTED_HOST}" \
    -r requirements.txt

# Chromium 仍写入镜像，只有下载地址切换为国内镜像；APT 依赖也复用同一份缓存。
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    PLAYWRIGHT_DOWNLOAD_HOST="${PLAYWRIGHT_DOWNLOAD_HOST}" playwright install --with-deps chromium

COPY . .
RUN mkdir -p data logs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
