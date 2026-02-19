# MBTI Stats Bot - 开发环境

这是 [`nonebot-plugin-mbtistats`](https://github.com/Siridelta/nonebot-plugin-mbtistats) 插件的开发和测试环境仓库。

本项目支持两种部署场景：
- **本地/服务器 + OneBot v11** - 主力开发场景，功能完整
- **腾讯云云函数 (SCF)** - 通过 Docker 容器化部署

## 项目结构

```
mbtistats-bot/
├── bot.py                      # NoneBot2 入口
├── pyproject.toml              # 项目依赖（editable install 插件）
├── Dockerfile                  # SCF 容器化部署
├── dev-plugins/
│   └── mbtistats/              # ← git submodule (插件源码)
├── scripts/
│   └── migrate_data_v1.py      # 数据迁移脚本
├── data/                       # 运行时数据（gitignored）
└── ...
```

## 快速开始

### 1. 克隆并初始化

```bash
git clone https://github.com/Siridelta/nonebot-plugin-mbtistats-devbot.git
cd mbtistats-bot
git submodule update --init
```

### 2. 安装依赖

```bash
uv sync
uv run playwright install chromium
```

### 3. 配置

复制 `.env.example` 为 `.env`，修改配置：

```env
# Bot 协议配置
DRIVER=~fastapi+~websockets
ONEBOT_WS_URLS=["ws://127.0.0.1:3001"]

# 插件配置
mbtistats_auto_stats_hour=0
mbtistats_auto_stats_minute=0
```

### 4. 运行

```bash
uv run bot.py
```

## 插件开发

插件源码位于 `dev-plugins/mbtistats/`（独立 git 仓库）。

编辑插件后提交：

```bash
cd dev-plugins/mbtistats
git add .
git commit -m "feat: xxx"
git push

cd ../..
git add dev-plugins/mbtistats
git commit -m "update: sync plugin"
git push
```

## SCF 部署（腾讯云云函数）

```bash
# 构建并推送镜像
docker build -t ccr.ccs.tencentyun.com/your-namespace/mbtistats-bot:latest .
docker push ccr.ccs.tencentyun.com/your-namespace/mbtistats-bot:latest

# 在 SCF 控制台使用自定义镜像部署
```

## 数据迁移

如果从旧版本升级，使用迁移脚本：

```bash
# 预览
python scripts/migrate_data_v1.py --dry-run

# 执行
python scripts/migrate_data_v1.py
```

## 相关仓库

- **插件源码**: [Siridelta/nonebot-plugin-mbtistats](https://github.com/Siridelta/nonebot-plugin-mbtistats)
- **开发环境**: 本仓库

## 技术栈

- Python 3.13
- NoneBot2 v2.4+
- uv (包管理)
- Playwright (图表渲染)
