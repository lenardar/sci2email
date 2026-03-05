# Sci2Email

Sci2Email 是一个 `FastAPI + React` 的 RSS 管理与邮件推送系统。

你可以把它当作：
- 一个可分组、可导入导出 OPML 的 RSS 管理后台
- 一个支持定时邮件推送的内容分发面板
- 一个带 AI 双语摘要能力（英文保留 + 中文译文）的 RSS 阅读器

## 核心功能

- 单管理员登录
- RSS 分组 / 订阅源管理
- OPML 导入 / 导出
- RSS 阅读器（筛选、搜索、查看原文）
- 推送任务管理（按订阅源精细推送、每日多个时间点）
- 收件人管理
- SMTP 图形化配置（系统发件邮箱、授权码）
- AI 图形化配置（API Key、模型、Base URL、超时）
- AI 双语处理：保留英文，同时展示中文标题和中文摘要
- 动态 AI 计算：
  - 阅读器中“看到哪条算哪条”
  - 推送时“发送前只算待发送内容”
- 拉取日志 / 发送日志

## 技术栈

- Backend: FastAPI, SQLAlchemy, APScheduler, SQLite
- Frontend: React, Vite, Ant Design
- Mail: SMTP
- AI: OpenAI-compatible Chat Completions API

## 项目结构

```text
sci2email/
  backend/
    app/
    requirements.txt
    .env.example
  frontend/
    src/
    package.json
  docker-compose.yml
```

## 本地启动

### 1) 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2) 启动前端（新终端）

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

访问地址：
- 前端: `http://127.0.0.1:5173`
- 后端健康检查: `http://127.0.0.1:8000/health`

默认登录：
- 用户名: `admin`
- 密码: `admin123`

## 配置说明

编辑 `backend/.env`：

### SMTP（邮件推送）

```env
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=your_email@163.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@163.com
SMTP_USE_TLS=true
```

> 也可以在页面 `推送管理 -> 系统推送邮箱配置` 里直接设置。

### AI（双语摘要）

```env
AI_ENABLED=true
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=30
```

> 推荐在页面 `推送管理 -> AI 配置` 中填写 API Key。页面配置会实时生效。

## 云端部署（Docker）

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填好 SMTP / AI / SECRET_KEY / ADMIN_PASSWORD

docker compose up -d --build
```

访问：
- 前端: `http://<server-ip>:5173`
- 后端: `http://<server-ip>:8000/health`

更新：

```bash
git pull
docker compose up -d --build
```

## OPML 使用

在 `RSS 管理 -> 源管理`：
- `导入 OPML`：批量导入订阅和分组
- `导出 OPML`：导出当前订阅配置

## AI 处理策略（当前）

- 新抓取文章默认 `ai_status=pending`
- 阅读器展开某条文章时，自动触发该条 AI 处理
- 推送任务执行时，对待发送文章自动补全 AI 双语摘要

## 常见问题

### 1) 前端打开的是另一个项目
通常是端口占用。请检查 `5173` 端口是否被其他进程占用。

### 2) AI 没生效
- 检查 `推送管理 -> AI 配置` 是否已保存 API Key
- 检查 `AI_ENABLED=true`
- 展开一条文章看 `AI` 状态是否 success/failed

### 3) 邮件发送失败
- 检查 SMTP 主机、端口、授权码
- 163/QQ/Gmail 常需要“应用专用密码”而不是登录密码

## License

MIT
