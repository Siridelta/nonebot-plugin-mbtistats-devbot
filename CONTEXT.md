# MBTI Stats Bot - 开发环境

这是 `nonebot-plugin-mbtistats` 插件的开发和测试环境仓库。

## 项目结构

```
mbtistats-bot/
├── bot.py                      # NoneBot2 入口文件
├── pyproject.toml              # 项目依赖配置
├── dev-plugins/
│   └── mbtistats/              # ← git submodule (插件源码)
│       ├── CONTEXT.md          # 详细的插件业务文档
│       ├── src/nonebot_plugin_mbtistats/
│       └── ...
└── data/                       # 运行时数据（gitignored）
```

## 快速开始

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

复制 `.env.example` 为 `.env`，按需修改：

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
- **包管理**: uv
- **Bot 框架**: NoneBot2 v2.4+
- **适配器**: OneBot v11 (主要), QQ (辅助)

## 依赖关系

```
mbtistats-bot (本仓库)
  └── nonebot-plugin-mbtistats (editable install)
       ├── nonebot2
       ├── nonebot-plugin-apscheduler
       ├── playwright
       └── jinja2
```
