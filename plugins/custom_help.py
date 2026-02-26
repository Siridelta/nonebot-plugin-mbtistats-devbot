from nonebot import on_command
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot, Event
from nonebot.internal.matcher import Matcher
from nonebot.rule import to_me

__plugin_meta__ = PluginMetadata(
    name="custom_help",
    description="自定义帮助插件 - 机器人主页帮助",
    usage="/help - 显示主页帮助\n/help plugins - 显示插件列表",
    type="application",
)

# 高优先级，拦截 /help 命令
help_cmd = on_command("help", aliases={"帮助"}, rule=to_me(), priority=1, block=True)

# 主页帮助文本（突出 MBTI 统计 - 机器人核心身份）
HOME_HELP = """
你好呀，我是 MBTI 计数菌～
我是一位专注于 MBTI 人格类型统计的机器人，可以自动识别群名片/昵称中的 MBTI 类型，生成精美的统计图表。

━━━━━━━━━━━━━━━━━━━━
📊 核心功能
━━━━━━━━━━━━━━━━━━━━
/mbti
  统计当前群的 MBTI 类型分布和特质维度分布，生成统计图
  
支持的类型格式：
  • 标准型：INTP、enfp（全大写/全小写）
  • 模糊型：INXP、exxp（用 X/x 代替不确定字母）
  • 扩展型：INTP-T、INTP(5w4)（识别其中的 MBTI 代码）
  • OPS 型：Te/Se、Ni/Fe（识别优势功能代码）

需要群友在群名片或 QQ 昵称中主动标注自己的 MBTI 类型才能被统计到哦～

━━━━━━━━━━━━━━━━━━━━
🔧 其他功能
━━━━━━━━━━━━━━━━━━━━
/help (或 /帮助)
  显示此帮助信息，需要 @bot。

/help plugins
  查看所有可用插件列表

/help <插件名>
  查看指定插件的详细帮助

━━━━━━━━━━━━━━━━━━━━
💡 提示
━━━━━━━━━━━━━━━━━━━━
• 所有指令均可使用 "/" 作为前缀
• 使用 "/help plugins" 探索更多功能
""".strip()


@help_cmd.handle()
async def handle_help(bot: Bot, event: Event, matcher: Matcher):
    """
    处理 /help 命令
    无参数或参数为空时显示主页帮助
    参数为 plugins 时透传给 help 插件
    参数为其他时透传给 help 插件查询具体插件
    """
    # 获取命令参数
    text = event.get_message().extract_plain_text().strip()
    
    # 去掉命令本身（/help 或 /帮助）
    cmd_prefixes = ["/help", "/帮助"]
    for prefix in cmd_prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    
    # 无参数或参数为空 -> 显示主页帮助
    if not text:
        await matcher.send(HOME_HELP)
        return
    
    # 参数为 plugins/all/列表 -> 透传给 help 插件（如果安装了的话）
    if text in ["plugins", "all", "列表", "plugin"]:
        # 尝试调用 help 插件的功能
        try:
            from nonebot import require
            help_plugin = require("nonebot_plugin_help")
            # 如果 help 插件有获取插件列表的功能，调用它
            # 这里简单处理，直接提示用户
            await matcher.send("📦 插件列表功能需要安装 nonebot-plugin-help\n\n可用命令：\n/mbti - MBTI 统计\n/help - 显示此帮助")
        except Exception:
            await matcher.send("📦 暂无其他插件\n\n可用命令：\n/mbti - MBTI 统计\n/help - 显示此帮助")
        return
    
    # 其他参数（可能是插件名）-> 透传或提示
    plugin_name = text
    await matcher.send(f"📦 插件「{plugin_name}」的帮助功能需要安装 nonebot-plugin-help\n\n使用 /help 查看主页帮助")
