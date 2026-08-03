# syntax=docker/dockerfile:1.7
FROM node:20-slim AS build
WORKDIR /app

# 1. 复制 package.json 和 npm 的 lock 文件
COPY package.json package-lock.json ./

# 2. 使用锁文件严格安装。下载缓存会保留在构建服务器，依赖变化时无需重复下载已有包。
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    npm ci --prefer-offline --no-audit

# 3. 复制其余项目文件并打包
COPY . .
RUN npm run build

# 第二阶段：Nginx 部署
FROM nginx:alpine
LABEL org.opencontainers.image.source="https://github.com/KInWonderland/miaozhu"
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
