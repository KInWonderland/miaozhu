FROM node:20-slim AS build
WORKDIR /app

# 1. 复制 package.json 和 npm 的 lock 文件
COPY package.json package-lock.json ./

# 2. 使用 npm ci 进行严格安装（相当于 pnpm 的 --frozen-lockfile，速度更快且更稳定）
RUN npm ci

# 3. 复制其余项目文件并打包
COPY . .
RUN npm run build

# 第二阶段：Nginx 部署
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
