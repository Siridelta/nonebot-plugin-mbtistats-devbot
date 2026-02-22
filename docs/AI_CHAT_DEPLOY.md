# MBTI 统计机器人 AI 对话功能部署指南

## 目录

1. [环境要求](#环境要求)
2. [依赖安装](#依赖安装)
3. [配置参数说明](#配置参数说明)
4. [启动流程](#启动流程)
5. [使用说明](#使用说明)
6. [常见问题排查](#常见问题排查)
7. [高级配置](#高级配置)

---

## 环境要求

### 基础环境

- **Python**: 3.13+
- **NoneBot2**: 2.4.4+
- **操作系统**: Windows / Linux / macOS

### 网络要求

- 能够访问 LLM API 服务（如 https://www.hubagi.cn）
- 推荐使用代理（如果服务器在大陆地区）

### 硬件要求

- 建议 2GB+ RAM
- 稳定网络连接

---

## 依赖安装

### 1. 安装项目依赖

```bash
# 安装所有依赖（包括新增的 openai）
uv sync
```

### 2. 验证 openai 库安装

```bash
uv run python -c "import openai; print(openai.__version__)"
```

### 3. 安装浏览器驱动（如需要 MBTI 统计功能）

```bash
uv run playwright install chromium
```

---

## 配置参数说明

### 配置文件位置

- 主配置: `.env`
- 示例配置: `.env.example`

### AI 对话配置项

| 参数名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `AI_ENABLED` | 否 | `true` | AI对话功能开关 |
| `AI_API_KEY` | 是 | - | LLM API 密钥 |
| `AI_BASE_URL` | 是 | - | API 基础URL |
| `AI_MODEL` | 否 | `ZP-glm-4.5-flash` | 模型名称 |
| `AI_MAX_HISTORY` | 否 | `10` | 对话历史轮数 |

### 配置示例

```env
# --- AI Chat ---

# AI对话功能开关
AI_ENABLED=true

# API密钥（从 hubagi 或其他 LLM 服务获取）
AI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# API基础URL
AI_BASE_URL=https://www.hubagi.cn/api/v1

# 模型名称
AI_MODEL=ZP-glm-4.5-flash

# 对话历史最大轮数
AI_MAX_HISTORY=10
```

### 获取 API 密钥

1. 访问 [Hubagi](https://www.hubagi.cn) 或其他支持的 LLM 服务
2. 注册账号并获取 API Key
3. 将 API Key 填入 `AI_API_KEY` 配置项

---

## 启动流程

### 1. 启动机器人

```bash
uv run bot.py
```

### 2. 验证启动成功

查看日志输出，确认以下信息：

```
AI对话功能已启用，模型: ZP-glm-4.5-flash, Base URL: https://www.hubagi.cn/api/v1
```

### 3. 测试 AI 对话

在群聊中 **@机器人** 发送中文消息（非 `/` 开头），例如：

```
@机器人 你好呀
```

机器人应该回复 AI 生成的内容。

---

## 使用说明

### 触发条件

AI 对话功能会在以下条件同时满足时触发：

1. 消息中 **@了机器人**
2. 消息内容为 **中文文本**
3. 消息 **不以 `/` 开头**（不与指令冲突）

### 可用指令

| 指令 | 说明 |
|------|------|
| `@机器人 + 中文消息` | 触发 AI 对话 |
| `清除记忆` | 清空当前对话历史 |
| `清空记忆` | 清空当前对话历史 |
| `重置对话` | 清空当前对话历史 |

### 对话上下文

- 机器人会记住当前会话（群聊或私聊）的对话历史
- 默认保留最近 10 轮对话
- 可通过 `AI_MAX_HISTORY` 配置调整

### 消息分割

AI 返回的消息中的 `<br>` 标签会被自动分割成多条消息发送。

---

## 常见问题排查

### 问题 1: "AI_API_KEY 未配置"

**症状**: 启动日志显示 "AI_API_KEY 未配置，AI对话功能将禁用"

**排查步骤**:

1. 确认 `.env` 文件中 `AI_API_KEY` 已正确填写
2. 检查配置项名称是否正确（注意大小写）
3. 重启机器人使配置生效
4. 检查是否有语法错误（如多余的空格或引号）

**解决方法**:

```env
# 正确格式
AI_API_KEY=sk-8d96bd3e...

# 错误格式（有空格）
AI_API_KEY = sk-8d96bd3e...

# 错误格式（有多余引号）
AI_API_KEY="sk-8d96bd3e..."
```

### 问题 2: "AI_BASE_URL 未配置"

**排查步骤**:

1. 确认 `AI_BASE_URL` 已填写
2. 检查 URL 格式是否正确（需要包含 `/v1` 后缀）

**正确示例**:

```
AI_BASE_URL=https://www.hubagi.cn/api/v1
```

### 问题 3: AI 对话不触发

**排查步骤**:

1. 确认已 @机器人
2. 确认消息是中文（包含中文字符）
3. 确认消息不是以 `/` 开头
4. 检查日志是否有错误信息

### 问题 4: API 调用失败

**可能原因**:

1. 网络问题 - 检查服务器网络能否访问 API 地址
2. API 密钥错误 - 确认密钥有效且未过期
3. 请求频率限制 - 稍后重试
4. API 服务不可用 - 检查服务商状态

**排查方法**:

```bash
# 测试 API 连接
curl -v https://www.hubagi.cn/api/v1
```

### 问题 5: 消息发送失败

**可能原因**:

1. 消息过长被平台限制
2. 包含敏感内容被拦截

---

## 高级配置

### 修改对话历史轮数

```env
AI_MAX_HISTORY=20
```

### 禁用 AI 对话功能

```env
AI_ENABLED=false
```

### 使用其他 LLM 模型

```env
AI_MODEL=gpt-3.5-turbo
AI_BASE_URL=https://api.openai.com/v1
```

### 调试模式

查看详细日志：

```env
LOG_LEVEL=DEBUG
```

---

## 架构说明

### 插件结构

```
plugins/ai_chat_plugin.py
├── 配置加载 (load_ai_config)
├── 触发检测 (is_valid_trigger, contains_chinese)
├── 对话管理 (add_to_history, clear_history)
├── API 调用 (call_ai_api)
├── 消息处理 (handle_ai_chat)
└── 消息分割 (split_message_by_br)
```

### 对话流程

```
用户发送消息
    ↓
检测 @机器人 + 中文 + 非指令
    ↓
加载对话历史
    ↓
调用 LLM API
    ↓
处理响应（按<br>分割）
    ↓
发送消息给用户
    ↓
保存对话历史
```

---

## 技术支持

如遇到无法解决的问题，请提供以下信息：

1. 机器人日志（包含错误信息的完整输出）
2. `.env` 配置（隐藏 API_KEY）
3. 操作系统和 Python 版本
4. 网络环境说明

---

## 更新日志

### v1.0.0

- 初始版本
- 支持 OneBot V11 / QQ / Console 适配器
- 实现对话上下文管理
- 实现 `<br>` 消息分割
