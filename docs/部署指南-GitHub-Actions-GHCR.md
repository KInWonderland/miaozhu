# GitHub Actions + 腾讯云 TCR 部署指南

本文将本项目部署为两个容器：`miaozhu-backend`（FastAPI）和 `miaozhu-frontend`（Nginx 静态站点与 API 反向代理）。部署链路为：向 `main` 推送代码，GitHub Actions 构建 Linux 镜像并推送至腾讯云容器镜像服务（TCR），服务器先在 `/home/ubuntu/env` 和 `/home/ubuntu/miaozhu` 执行 `git pull`，再从 TCR 拉取该提交对应的镜像并使用 Docker Compose 重启服务。

本地开发继续使用 `docker-compose.yml`；服务器使用 `docker-compose.prod.yml`。它们共用 `backend/Dockerfile` 与 `frontend/Dockerfile`，无需维护两套 Dockerfile。

## 一、首次准备服务器

以下示例以 Ubuntu/Debian 服务器、`/home/ubuntu/miaozhu` 为部署目录、`/home/ubuntu/env` 为已克隆的环境配置 Git 仓库（其中包含 `miaozhu/.env`）、`/var/lib/miaozhuData` 为数据库与导出文件持久化目录。服务器需要可访问对应的 TCR 实例，并安装 Docker Engine 与 Docker Compose Plugin。确认命令如下：

```bash
docker --version
docker compose version
```

创建部署目录和数据目录，并将环境配置仓库克隆到 `/home/ubuntu/env`：

```bash
sudo mkdir -p /home/ubuntu/miaozhu /var/lib/miaozhuData
sudo chown -R ubuntu:ubuntu /home/ubuntu/miaozhu /var/lib/miaozhuData
git clone <环境配置仓库地址> /home/ubuntu/env
sudo chown -R ubuntu:ubuntu /home/ubuntu/env
```

将仓库中的 `docker-compose.prod.yml` 复制到 `/home/ubuntu/miaozhu/docker-compose.prod.yml`。首次可使用 `scp`，之后此文件通常不需要改动：

```bash
scp docker-compose.prod.yml ubuntu@<服务器地址>:/home/ubuntu/miaozhu/
```

在服务器创建 `/home/ubuntu/env/miaozhu/.env`，从项目的 `backend/.env.example` 复制需要的配置并填写真实值。至少应配置 LLM 相关变量；生产域名部署时还应把 `CORS_ORIGINS` 改为实际来源。此文件包含密钥，只留在服务器，不能提交 Git。

```bash
nano /home/ubuntu/env/miaozhu/.env
chmod 600 /home/ubuntu/env/miaozhu/.env
```

## 二、配置腾讯云 TCR 凭据

在 TCR 控制台创建一个有目标命名空间推送和拉取权限的服务级账号或用户级账号。工作流会在 GitHub Runner 和部署服务器上使用该凭据登录 TCR；无需在服务器手动保存凭据。不要把用户名或密码写入仓库、Compose 文件或日志。

TCR 企业版 Registry 地址通常形如 `<实例名>.tencentcloudcr.com`；请在实例控制台的“访问凭证”中复制实际登录地址与凭据。

首次工作流成功之前镜像不存在，故此时不必执行 `docker compose up`。

## 三、配置 GitHub Actions Secrets

在仓库的 **Settings → Secrets and variables → Actions** 中新增以下 Repository secrets：

| 名称 | 填写内容 |
| --- | --- |
| `SERVER_HOST` | 服务器公网 IP 或域名 |
| `SERVER_USER` | 登录服务器的普通用户，例如 `ubuntu` |
| `SERVER_SSH_KEY` | 该用户的私钥全文（推荐专为部署新建一对密钥） |
| `TCR_USERNAME` | TCR 服务级或用户级账号的用户名 |
| `TCR_PASSWORD` | 上述 TCR 账号的密码或访问令牌 |
| `TELEGRAM_TO` | 接收部署通知的 Telegram chat ID |
| `TELEGRAM_TOKEN` | Telegram BotFather 创建的机器人 Token |

同时在 **Settings → Secrets and variables → Actions → Variables** 中新增：

| 名称 | 填写内容 |
| --- | --- |
| `TCR_REGISTRY` | TCR 实例域名，例如 `demo-tcr.tencentcloudcr.com` |
| `TCR_NAMESPACE` | 已创建的 TCR 命名空间，例如 `miaozhu` |

工作流默认使用 SSH 端口 `22`，部署路径固定为 `/home/ubuntu/miaozhu`。若服务器 SSH 使用其他端口，需要在 `.github/workflows/deploy.yml` 的 SSH 步骤中显式添加 `port` 配置。

创建部署密钥的示例：

```bash
ssh-keygen -t ed25519 -C "github-actions-miaozhu-deploy"
```

将公钥内容追加到服务器目标用户的 `~/.ssh/authorized_keys`；私钥全文填入 `SERVER_SSH_KEY`。建议该用户仅拥有维护 `/home/ubuntu/miaozhu`、`/var/lib/miaozhuData` 和运行 Docker 的必要权限，并关闭密码登录。

## 四、首次发布

确认工作流文件、生产 Compose 文件和 Docker 忽略文件已提交至默认分支，然后推送：

```bash
git add .github/workflows/deploy.yml docker-compose.prod.yml backend/.dockerignore frontend/.dockerignore docker-compose.yml docs/部署指南-GitHub-Actions-GHCR.md
git commit -m "ci: deploy Docker images through TCR"
git push origin main
```

进入 GitHub 仓库 **Actions → Build and deploy** 查看运行日志。构建完成后，工作流会分别推送以下镜像标签：

```text
<TCR_REGISTRY>/<TCR_NAMESPACE>/miaozhu-backend:<commit-sha>
<TCR_REGISTRY>/<TCR_NAMESPACE>/miaozhu-frontend:<commit-sha>
```

服务器随后拉取同一个 `<commit-sha>` 并启动，前端默认暴露在 `http://<服务器地址>/`。后端不直接暴露公网端口，仅由前端 Nginx 转发 `/api/` 请求。服务成功启动后，工作流会向 `TELEGRAM_TO` 指定的聊天发送仓库、提交 SHA 和服务器地址。

## 五、日常发布、检查与回滚

以后每次向 `main` 推送，都会自动发布。每次发布都会先在 `/home/ubuntu/env` 和 `/home/ubuntu/miaozhu` 执行 `git pull`，然后登录 TCR 并拉取镜像；因此这两个目录须是部署用户可访问的 Git 工作树，且已配置好拉取远程仓库所需的认证。可在服务器检查状态和日志：

```bash
cd /home/ubuntu/miaozhu
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

回滚时，从 GitHub 的某次成功工作流或提交记录中找到之前的完整 commit SHA，在服务器执行：

```bash
cd /home/ubuntu/miaozhu
TCR_REGISTRY=<实例域名> TCR_NAMESPACE=<命名空间> IMAGE_TAG=<之前的完整commit-sha> docker compose -f docker-compose.prod.yml pull
TCR_REGISTRY=<实例域名> TCR_NAMESPACE=<命名空间> IMAGE_TAG=<之前的完整commit-sha> docker compose -f docker-compose.prod.yml up -d
```

`/var/lib/miaozhuData` 是数据库与导出文件的持久化目录，升级与回滚容器都不会删除它。升级前应定期备份：

```bash
sudo tar -C /var/lib -czf ~/miaozhu-data-$(date +%F).tar.gz miaozhuData
```

## 六、常见问题

**Actions 可以构建镜像，但服务器拉取失败**：确认 `TCR_REGISTRY`、`TCR_NAMESPACE`、`TCR_USERNAME` 和 `TCR_PASSWORD` 已正确配置，账号具有目标命名空间的拉取权限，且服务器网络可访问 TCR 实例。

**容器启动后页面无法打开**：检查服务器的 80 端口是否已被 Nginx、Caddy 或其他服务占用；如已有反向代理，应把生产 Compose 的前端端口映射改为 `127.0.0.1:8080:80`，再由反向代理转发。

**后端报 LLM 配置错误**：检查 `/home/ubuntu/env/miaozhu/.env` 的值和文件权限；不要将该文件复制进 Docker 镜像。

**本地能跑、服务器启动失败**：本工作流构建的是 `linux/amd64` 镜像，适用于多数 x86_64 云服务器。若服务器为 ARM64，请将工作流中的 `platforms: linux/amd64` 改为 `linux/arm64`，或构建多架构镜像。
