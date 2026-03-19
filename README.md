> 🔥 **承接软件外包开发**
> 
> 微信小程序 · 安卓/iOS APP · 企业管理系统
> 
> 📱 **合作联系：** `tuhoooo`（微信）
> 
> 💰 **介绍项目有丰厚分佣，欢迎合作！**

# 秒著 - AI 软著材料生成工具

AI 驱动的软件著作权申请材料自动生成工具。填写软件基本信息后，AI 自动生成操作说明书、源程序代码等软著申请所需的全部材料，支持导出 Word/PDF 格式。

## 功能特性

- **AI 智能生成**：基于软件信息自动生成操作说明书、源程序代码、数据库设计等材料
- **多格式导出**：支持 Word、PDF 格式导出，支持打包下载
- **实时进度**：SSE 实时推送生成进度，章节级别的状态跟踪
- **在线编辑**：生成结果支持在线 Markdown 编辑和实时预览
- **章节重新生成**：对不满意的章节可单独重新生成
- **图表生成**：可选生成流程图、ER 图等 Mermaid 图表
- **额外指令**：支持自定义生成指令，控制生成内容的方向和风格
- **通用 LLM**：兼容任何 OpenAI API 格式的大语言模型
- **开箱即用**：SQLite 嵌入式数据库，无需安装 MySQL/Redis，启动即用

## 技术栈

**后端**：FastAPI + SQLAlchemy (async) + SQLite (aiosqlite)

**前端**：Vue 3 + TypeScript + Element Plus + Pinia + Vite

## 前置要求

- Python 3.11+
- Node.js 18+ & pnpm
- OpenAI 兼容的 LLM API（如 OpenAI、DeepSeek、通义千问等）

> 不需要 MySQL、Redis 或其他外部服务。数据库使用 SQLite，首次启动时自动创建。

---

## 快速开始

### 1. 克隆项目

```bash
git clone <repo-url>
cd miaozhu
```

### 2. 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

如果需要图表渲染功能（可选），安装 Playwright 浏览器：

```bash
playwright install chromium
```

复制环境配置并编辑：

```bash
cp .env.example .env
```

编辑 `.env`，填入 LLM API 配置（**必填项只有 3 个**）：

```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key
LLM_MODEL=gpt-4o
```

启动后端：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

首次启动会自动在 `data/` 目录下创建 SQLite 数据库文件，无需手动初始化。

### 3. 前端

```bash
cd frontend
pnpm install
pnpm dev
```

访问 http://localhost:5173 即可使用。

> 开发模式下，前端通过 Vite 代理自动将 `/api` 请求转发到 `http://localhost:8000`。

---

## 使用指南

### 基本流程

1. **新建申请**：在「软著申请」页面点击新建，填写软件名称、简称、主要功能等基本信息
2. **完善信息**（可选）：补充开发语言、运行环境、权利信息、申请人信息等
3. **AI 生成**：点击生成按钮，AI 会自动生成以下材料：
   - 操作说明书（包含多个章节：软件概述、安装部署、功能模块详细说明等）
   - 源程序代码（前 30 页 + 后 30 页格式）
   - 数据库设计文档（可选）
4. **在线编辑**：对生成结果不满意的章节，可以直接在线编辑 Markdown 内容
5. **章节重新生成**：也可以对单个章节提交重新生成，支持附加额外指令引导 AI
6. **导出下载**：生成完成后，支持导出为 Word 或 PDF 格式

### 生成选项

新建申请时可以选择：

- **生成源程序代码**：默认开启，生成符合软著申请要求的源代码材料
- **生成数据库设计**：默认开启，生成数据库表结构和 ER 图
- **生成图表**：可选开启，在操作说明书中嵌入 Mermaid 流程图和架构图

### 额外指令

在生成时可以填写「额外指令」来引导 AI 的生成方向，例如：

- "使用 Java Spring Boot 框架风格"
- "源代码使用 Python，包含完整的错误处理"
- "操作说明书中着重描述数据分析和报表功能"

### 导出格式

| 格式 | 说明 |
|------|------|
| 文档鉴别材料 (Word/PDF) | 操作说明书，含目录、页眉页脚 |
| 源程序鉴别材料 (Word/PDF) | 源代码前后各 30 页 |
| 全部材料 (ZIP) | 打包下载以上所有格式 |

### 状态流转

申请的完整状态流：

```
草稿 → 生成中 → 已生成 → 准备提交 → 已提交 → 已通过
                  ↘ 返回编辑       ↘ 返回审核    ↘ 已驳回 → 重新修改
                                                          → 归档
```

---

## 配置说明

所有配置通过 `backend/.env` 文件管理：

### LLM 配置（必填）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_BASE_URL` | OpenAI 兼容 API 地址 | `https://api.openai.com/v1` |
| `LLM_API_KEY` | API 密钥 | （无） |
| `LLM_MODEL` | 模型名称 | `gpt-4o` |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CORS_ORIGINS` | 允许的前端域名（JSON 数组） | `["http://localhost:5173"]` |
| `DATABASE_URL` | 数据库连接地址 | `sqlite+aiosqlite:///data/miaozhu.db` |
| `EXPORT_DATA_DIR` | 导出文件存储目录 | `data/exports` |
| `SCHEDULER_POLL_INTERVAL` | 调度器轮询间隔（秒） | `5` |
| `SCHEDULER_MAX_CONCURRENT_LLM` | 最大并发 LLM 调用数 | `5` |
| `SCHEDULER_MAX_CONCURRENT_EXPORT` | 最大并发导出任务数 | `4` |

### LLM 模型选择

项目使用通用的 OpenAI Chat Completions 兼容接口，支持任何提供该格式 API 的服务商和模型。

**模型要求**：生成软著材料涉及长篇中文文档和代码，建议选择中文能力强、支持长输出的模型。小参数量模型（7B 以下）可能生成质量不足。

#### OpenAI

| 模型 | 说明 |
|------|------|
| `gpt-4o` | 推荐，综合能力强，性价比高 |
| `gpt-4o-mini` | 更便宜，速度更快，质量略低 |
| `o3-mini` | 推理模型，适合复杂逻辑但速度较慢 |

```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key
LLM_MODEL=gpt-4o
```

#### DeepSeek

| 模型 | 说明 |
|------|------|
| `deepseek-chat` | 推荐，中文和代码能力优秀，价格低 |
| `deepseek-reasoner` | 推理模型，适合复杂场景 |

```bash
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-api-key
LLM_MODEL=deepseek-chat
```

#### 通义千问（阿里云）

| 模型 | 说明 |
|------|------|
| `qwen-plus` | 推荐，均衡之选 |
| `qwen-turbo` | 更快更便宜，适合对质量要求不高的场景 |
| `qwen-max` | 最强能力，价格较高 |

```bash
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-your-api-key
LLM_MODEL=qwen-plus
```

#### 智谱 GLM（智谱 AI）

| 模型 | 说明 |
|------|------|
| `glm-4-plus` | 推荐，中文能力强 |
| `glm-4-flash` | 免费额度大，速度快 |

```bash
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_API_KEY=your-api-key
LLM_MODEL=glm-4-plus
```

#### 月之暗面 Kimi

| 模型 | 说明 |
|------|------|
| `moonshot-v1-8k` | 标准版 |
| `moonshot-v1-32k` | 长上下文 |

```bash
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_API_KEY=sk-your-api-key
LLM_MODEL=moonshot-v1-8k
```

#### 百度文心一言

| 模型 | 说明 |
|------|------|
| `ernie-4.0-8k` | 旗舰模型 |
| `ernie-3.5-8k` | 性价比之选 |

```bash
LLM_BASE_URL=https://qianfan.baidubce.com/v2
LLM_API_KEY=your-api-key
LLM_MODEL=ernie-4.0-8k
```

#### 本地部署（Ollama）

适合对数据隐私有要求、不想调用云端 API 的场景。建议 14B 及以上参数量的模型。

| 模型 | 说明 |
|------|------|
| `qwen2.5:14b` | 推荐，中文能力好 |
| `qwen2.5:32b` | 更强，需要较大显存 |
| `deepseek-v2:16b` | 代码能力突出 |

```bash
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:14b
```

> Ollama 安装后运行 `ollama pull qwen2.5:14b` 即可下载模型。

#### 其他兼容服务

任何提供 OpenAI Chat Completions 格式（`POST /v1/chat/completions`）的服务均可接入，包括 vLLM、LocalAI、LiteLLM、OpenRouter、硅基流动（SiliconFlow）等。只需正确填写 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 三项即可。

---

## 生产部署

### 方式一：直接部署

适用于单台服务器（推荐 2C4G 及以上配置）。

#### 1. 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium  # 可选，图表渲染需要

cp .env.example .env
# 编辑 .env 填入 LLM 配置
```

启动后端服务（推荐使用单进程，SQLite 不适合多 worker 并发写入）：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

使用 systemd 管理服务：

```ini
# /etc/systemd/system/miaozhu.service
[Unit]
Description=Miaozhu API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/miaozhu/backend
Environment=PATH=/opt/miaozhu/backend/venv/bin
ExecStart=/opt/miaozhu/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable miaozhu
sudo systemctl start miaozhu
```

#### 2. 前端

```bash
cd frontend
pnpm install
pnpm build
```

构建产物在 `frontend/dist/` 目录，部署到 Nginx：

```bash
sudo cp -r dist/ /var/www/miaozhu/
```

#### 3. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/miaozhu;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;  # 生成和导出可能较慢
    }

    # SSE 需要关闭缓冲
    location /api/v1/sse/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
    }
}
```

配置 HTTPS（推荐）：

```bash
sudo apt install certbot python3-certbot-nginx  # Debian/Ubuntu
sudo certbot --nginx -d your-domain.com
```

别忘了在 `.env` 中设置 CORS 为实际域名：

```bash
CORS_ORIGINS=["https://your-domain.com"]
```

### 方式二：Docker 部署

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data        # 持久化数据库和导出文件
      - ./backend/.env:/app/.env  # 环境配置
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

后端 `backend/Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

COPY . .
RUN mkdir -p data logs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

前端 `frontend/Dockerfile`：

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

前端 `frontend/nginx.conf`：

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location /api/v1/sse/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
    }
}
```

启动：

```bash
docker compose up -d
```

---

## 数据管理

### 数据文件

所有数据存储在 `backend/data/` 目录下：

```
backend/data/
├── miaozhu.db      # SQLite 数据库（所有申请和生成数据）
└── exports/         # 导出的 Word/PDF 文件
```

### 备份

备份只需复制 `data/` 目录即可：

```bash
# 备份
cp -r backend/data/ backup/miaozhu-data-$(date +%Y%m%d)/

# 恢复
cp -r backup/miaozhu-data-20260302/ backend/data/
```

> SQLite 使用 WAL 模式，备份时建议先停止服务以确保数据完整性。如需在线备份，可使用 `sqlite3` 的 `.backup` 命令。

### 重置数据

删除数据库文件后重启服务即可自动重建空表：

```bash
rm backend/data/miaozhu.db
# 重启后端服务
```

---

## 项目结构

```
miaozhu/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 路由
│   │   ├── core/            # 配置、数据库、依赖注入
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # 业务逻辑层
│   │       ├── llm/         # LLM 提供者抽象
│   │       ├── generation/  # 内容生成调度
│   │       ├── export/      # 文档导出调度
│   │       └── prompts/     # LLM 提示词构建
│   ├── data/                # SQLite 数据库和导出文件（自动创建）
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/             # API 客户端
    │   ├── components/      # 公共组件
    │   ├── layouts/         # 布局组件
    │   ├── router/          # 路由配置
    │   ├── stores/          # Pinia 状态管理
    │   ├── utils/           # 工具函数
    │   └── views/           # 页面视图
    └── package.json
```

## 常见问题

**Q: 生成速度慢？**

生成速度取决于 LLM API 的响应速度。一个完整的软著材料包含十多个章节，每个章节需要一次 LLM 调用。可以通过调整 `SCHEDULER_MAX_CONCURRENT_LLM` 增加并发数来加速（默认 5）。

**Q: 导出 PDF 失败？**

PDF 导出依赖 Playwright 浏览器引擎。请确保已运行 `playwright install chromium`。在服务器上可能需要额外安装系统依赖：`playwright install --with-deps chromium`。

**Q: 如何更换 LLM 模型？**

修改 `.env` 中的 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 三项即可，无需重启服务（下次生成任务会使用新配置）。支持任何兼容 OpenAI Chat Completions API 的服务。

**Q: 数据库文件越来越大？**

可以定期清理旧的导出文件：`rm -rf backend/data/exports/*`。如果数据库本身过大，可以用 `sqlite3 backend/data/miaozhu.db "VACUUM;"` 压缩。

## 请我喝杯咖啡

如果这个项目对你有帮助，欢迎请我喝杯美式深烘 :)

<img src="frontend/public/wechat-pay.jpg" alt="微信收款码" width="300" />

## License

本项目基于 [Apache License 2.0](LICENSE) 开源。
