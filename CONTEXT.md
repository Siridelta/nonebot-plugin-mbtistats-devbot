# MBTI Stats Bot - 开发环境

这是 `nonebot-plugin-mbtistats` 插件的开发和测试环境仓库，兼作整机部署（部署整个 Bot 的场景，如家庭服务器、SCF、Docker等）的内容。

本仓库支持两种部署/运行场景：
- **场景 A：腾讯云云函数 (SCF)** - 需要 Docker 容器化部署整个 Bot
- **场景 B：本地/服务器 + OneBot v11** - 当前主力开发场景

## 项目结构

```
mbtistats-bot/
├── bot.py                      # NoneBot2 入口文件
├── pyproject.toml              # 项目依赖配置
├── Dockerfile                  # ← SCF 场景需要
├── dev-plugins/
│   └── mbtistats/              # ← git submodule (插件源码)
│       ├── CONTEXT.md          # 详细的插件业务文档
│       ├── src/nonebot_plugin_mbtistats/
│       └── ...
└── data/                       # 运行时数据（gitignored）
```

## 快速开始（场景 B：本地开发）

### 1. 克隆并初始化 submodule

```bash
git clone https://github.com/Siridelta/nonebot-plugin-mbtistats-devbot.git
cd mbtistats-bot
git submodule update --init
```

### 2. 安装依赖

```bash
uv sync
```

这会通过 editable install 安装插件及其所有依赖。

### 3. 配置环境变量

复制 `.env.example` 为 `.env`：

```env
# Bot 协议配置
DRIVER=~fastapi+~websockets
ONEBOT_WS_URLS=["ws://127.0.0.1:3001"]

# 可选：自动统计配置
auto_stats_debug=false
auto_stats_run_on_startup=false
```

### 4. 运行

```bash
uv run bot.py
```

## 部署场景 A：腾讯云云函数 (SCF)

**架构说明**：

由于腾讯云 SCF 基础环境限制（CentOS 7/glibc 版本过低），本项目采用 **Docker 容器化部署** 方案：

```
Docker 镜像 → 腾讯云镜像仓库 (TCR) → 腾讯云函数 (SCF) Web 函数模式
```

**镜像大小限制**：SCF 要求解压前 ≤ 1GB。
- 粗略估算：Python Slim (~120MB) + Chromium (~300MB) + 依赖 ≈ 600-800MB，可以塞入。

### Dockerfile

```dockerfile
# 使用官方 Python Slim 基础镜像
FROM python:3.13-slim

# 安装 Chromium 依赖和字体
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    fonts-wqy-zenhei fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -e ./dev-plugins/mbtistats

# SCF 启动命令
CMD ["python", "bot.py"]
```

### 部署步骤

```bash
# 1. 构建镜像
docker build -t ccr.ccs.tencentyun.com/your-namespace/mbtistats-bot:latest .

# 2. 推送到腾讯云镜像仓库
docker push ccr.ccs.tencentyun.com/your-namespace/mbtistats-bot:latest

# 3. 在 SCF 控制台创建 Web 函数，选择自定义镜像部署
# 4. 配置环境变量（QQ_APP_ID, QQ_TOKEN 等）
```

**注意**：SCF 场景下，插件的 `editable install` 会变成普通安装（因为 Docker 构建时会复制整个插件目录）。

## 插件开发

插件源码位于 `dev-plugins/mbtistats/`（submodule）。

编辑插件代码后，直接在 submodule 内提交：

```bash
cd dev-plugins/mbtistats
# 编辑代码...
git add .
git commit -m "feat: xxx"
git push

# 回到外层更新 submodule 指针
cd ../..
git add dev-plugins/mbtistats
git commit -m "update: sync plugin submodule"
```

## 文档

- **插件业务逻辑/API/模板**：见 `dev-plugins/mbtistats/CONTEXT.md`
- **插件 README**：见 `dev-plugins/mbtistats/README.md`

## 技术栈

- **Python**: 3.13
- **包管理**: uv (本地), pip (Docker)
- **Bot 框架**: NoneBot2 v2.4+
- **适配器**: OneBot v11 (主要), QQ (辅助/SCF场景)
- **容器**: Docker (SCF 场景)

## 依赖关系

```
mbtistats-bot (本仓库)
  └── nonebot-plugin-mbtistats (editable install / Docker COPY)
       ├── nonebot2
       ├── nonebot-plugin-apscheduler
       ├── playwright
       └── jinja2
```
