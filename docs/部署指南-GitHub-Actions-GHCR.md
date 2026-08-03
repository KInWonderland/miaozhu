# GitHub Actions + 腾讯云服务器本机构建部署指南

本文将本项目部署为两个容器：`miaozhu-backend`（FastAPI）和 `miaozhu-frontend`（Nginx 静态站点与 API 反向代理）。部署链路为：向 `main` 推送代码，GitHub Actions 通过 SSH 连接腾讯云服务器；服务器在 `/home/ubuntu/env` 和 `/home/ubuntu/miaozhu` 执行 `git pull --ff-only` 获取最新代码，然后在服务器本机构建 Docker 镜像并使用 Docker Compose 重启服务。

本地开发继续使用 `docker-compose.yml`；服务器使用 `docker-compose.prod.yml`。它们共用 `backend/Dockerfile` 与 `frontend/Dockerfile`，无需维护两套 Dockerfile。

## 一、首次准备服务器

以下示例以 Ubuntu/Debian 服务器、`/home/ubuntu/miaozhu` 为部署目录、`/home/ubuntu/env` 为已克隆的环境配置 Git 仓库（其中包含 `miaozhu/.env`）、`/var/lib/miaozhuData` 为数据库与导出文件持久化目录。服务器需要安装 Docker Engine、Docker Compose Plugin 和 Git，并能够从 GitHub 拉取代码。确认命令如下：

```bash
docker --version
docker compose version
git --version
```

创建部署目录和数据目录，并将项目仓库与环境配置仓库分别克隆到服务器：

```bash
sudo mkdir -p /home/ubuntu/miaozhu /var/lib/miaozhuData
sudo chown -R ubuntu:ubuntu /home/ubuntu/miaozhu /var/lib/miaozhuData
git clone <项目仓库地址> /home/ubuntu/miaozhu
git clone <环境配置仓库地址> /home/ubuntu/env
sudo chown -R ubuntu:ubuntu /home/ubuntu/env
```

在服务器创建 `/home/ubuntu/env/miaozhu/.env`，从项目的 `backend/.env.example` 复制需要的配置并填写真实值。至少应配置 LLM 相关变量；生产域名部署时还应把 `CORS_ORIGINS` 改为实际来源。此文件包含密钥，只留在服务器，不能提交 Git。

```bash
nano /home/ubuntu/env/miaozhu/.env
chmod 600 /home/ubuntu/env/miaozhu/.env
```

## 二、配置服务器的 Git 拉取权限

部署工作流不会再推送或拉取镜像仓库。请让服务器上的 `ubuntu` 用户拥有项目仓库和环境配置仓库的只读拉取权限；私有仓库推荐为服务器创建专用 SSH 密钥，并将公钥添加为 GitHub Deploy Key 或有只读权限的机器用户 SSH Key。

在服务器上验证两个目录均可无交互拉取：

```bash
cd /home/ubuntu/miaozhu && git pull --ff-only
cd /home/ubuntu/env && git pull --ff-only
```

## 三、配置现有 Nginx 反向代理

生产容器只监听服务器本机的 `127.0.0.1:5173`，不再直接占用公网 80 端口。请保留服务器已有的 Nginx，并在对应站点的 `server` 块中加入以下配置（将 `<你的域名>` 替换为实际域名）：

```nginx
server {
    listen 80;
    server_name <你的域名>;

    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

保存配置后在服务器验证并重载 Nginx：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 四、配置 GitHub Actions Secrets

在仓库的 **Settings → Secrets and variables → Actions** 中新增以下 Repository secrets：

| 名称 | 填写内容 |
| --- | --- |
| `SERVER_HOST` | 服务器公网 IP 或域名 |
| `SERVER_USER` | 登录服务器的普通用户，例如 `ubuntu` |
| `SERVER_SSH_KEY` | 该用户的私钥全文（推荐专为部署新建一对密钥） |
| `TELEGRAM_TO` | 接收部署通知的 Telegram chat ID |
| `TELEGRAM_TOKEN` | Telegram BotFather 创建的机器人 Token |

工作流默认使用 SSH 端口 `22`，部署路径固定为 `/home/ubuntu/miaozhu`。若服务器 SSH 使用其他端口，需要在 `.github/workflows/deploy.yml` 的 SSH 步骤中显式添加 `port` 配置。

创建部署密钥的示例：

```bash
ssh-keygen -t ed25519 -C "github-actions-miaozhu-deploy"
```

将公钥内容追加到服务器目标用户的 `~/.ssh/authorized_keys`；私钥全文填入 `SERVER_SSH_KEY`。建议该用户仅拥有维护 `/home/ubuntu/miaozhu`、`/var/lib/miaozhuData` 和运行 Docker 的必要权限，并关闭密码登录。

## 五、首次发布

确认工作流文件、生产 Compose 文件和 Docker 忽略文件已提交至默认分支，然后推送：

```bash
git add .github/workflows/deploy.yml docker-compose.prod.yml README.md docs/部署指南-GitHub-Actions-GHCR.md
git commit -m "ci: build containers on deployment server"
git push origin main
```

进入 GitHub 仓库 **Actions → Deploy to Tencent Cloud** 查看运行日志。服务器拉取最新代码后，会使用 `docker compose -f docker-compose.prod.yml up -d --build --remove-orphans` 在本机构建镜像并启动容器。前端默认暴露在 `http://<服务器地址>/`，后端不直接暴露公网端口，仅由前端 Nginx 转发 `/api/` 请求。服务成功启动后，工作流会向 `TELEGRAM_TO` 指定的聊天发送仓库、提交 SHA 和服务器地址。

## 六、日常发布、检查与回滚

以后每次向 `main` 推送，都会自动发布。每次发布都会先在 `/home/ubuntu/env` 和 `/home/ubuntu/miaozhu` 执行 `git pull --ff-only`，再在腾讯云服务器上构建镜像并重启容器；因此这两个目录须是部署用户可访问的 Git 工作树，且已配置好拉取远程仓库所需的认证。可在服务器检查状态和日志：

```bash
cd /home/ubuntu/miaozhu
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

回滚时，从 GitHub 的提交记录中找到目标提交，在服务器执行：

```bash
cd /home/ubuntu/miaozhu
git fetch origin
git checkout <目标提交SHA>
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
```

回滚完成后，请执行 `git checkout main`，以保证后续自动部署可以正常执行 `git pull --ff-only`。

`/var/lib/miaozhuData` 是数据库与导出文件的持久化目录，升级与回滚容器都不会删除它。升级前应定期备份：

```bash
sudo tar -C /var/lib -czf ~/miaozhu-data-$(date +%F).tar.gz miaozhuData
```

## 七、常见问题

**Actions 连接服务器后 `git pull` 失败**：确认服务器上的 `ubuntu` 用户能无交互拉取 `/home/ubuntu/miaozhu` 与 `/home/ubuntu/env` 中的 Git 仓库；私有仓库还要确认部署密钥已被 GitHub 授权。

**容器启动后页面无法打开**：确认 Nginx 已将请求转发至 `http://127.0.0.1:5173`，并使用 `docker compose -f docker-compose.prod.yml ps` 检查前端容器是否正在运行。

**后端报 LLM 配置错误**：检查 `/home/ubuntu/env/miaozhu/.env` 的值和文件权限；不要将该文件复制进 Docker 镜像。

**本地能跑、服务器启动失败**：镜像现在由服务器本机构建，Docker 会自动使用该服务器的 CPU 架构。请确认服务器有足够的磁盘空间与内存完成依赖安装和镜像构建。
