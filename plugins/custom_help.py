from typing import Set

from nonebot import on_command, get_driver
from nonebot.plugin import PluginMetadata, get_loaded_plugins
from nonebot.adapters import Bot, Event
from nonebot.internal.matcher import Matcher
from nonebot.rule import to_me
from pydantic import BaseModel, Field


class HelpConfig(BaseModel):
    """帮助插件配置 - 白名单机制"""
    help_visible_plugins: Set[str] = Field(
        default_factory=set,
        description="在插件列表中显示的插件包名（白名单），为空则显示所有插件"
    )


# 获取配置
help_config = None
try:
    driver = get_driver()
    from nonebot.plugin import get_plugin_config
    help_config = get_plugin_config(HelpConfig)
except Exception:
    # 配置加载失败时使用默认
    help_config = HelpConfig()


__plugin_meta__ = PluginMetadata(
    name="custom_help",
    description="自定义帮助插件 - 机器人主页帮助",
    usage="/help - 显示主页帮助\n/help plugins - 显示插件列表",
    type="application",
)

# 高优先级，拦截 /help 命令
help_cmd = on_command("help", aliases={"帮助"}, priority=1, block=True)
''''''
def get_home_help() -> str:
    """动态生成主页帮助文本，包含所有插件命令"""
    
    # 基础介绍
    help_text = """
你好呀，我是 MBTI 计数菌～
我是一位专注于 MBTI 人格类型统计的机器人，可以自动识别群名片/昵称中的 MBTI 类型，生成统计图表。

📊 核心功能
• /mbti
    统计当前群的 MBTI 类型分布和特质维度分布，生成统计图
• 支持的类型格式：
    • 标准型：INTP、enfp（全大写/全小写）
    • 模糊型：INXP、exxp（用 X/x 代替不确定字母）
    • 扩展型：INTP-T、INTP(5w4)（识别其中的 MBTI 代码）
    • OPS 型：Te/Se、Ni/Fe（识别优势功能代码）
• 需要群友在群名片或 QQ 昵称中主动标注自己的 MBTI 类型才能被统计到哦～
""".strip()
    
    # 动态获取所有插件的命令
    plugin_commands = []
    
    # 手动添加已知的核心命令（确保顺序和描述准确）
    core_commands = [
        ("/运势", "测运势", "查看今日MBTI运势（可带生日获得更个性化结果）"),
        ("/timer", "timer", "设置倒计时提醒，如：/timer 5m 喝水"),
        ("/eval", 'eval', '执行Python语法计算，包括但不限于普通运算和简易数据操作'),
        ("/recall", "recall", "撤回机器人最近发送的消息"),
    ]
    
    for cmd, name, desc in core_commands:
        plugin_commands.append(f"• {cmd}\n    {desc}")
    
    # 添加AI对话说明
    plugin_commands.append("• @机器人 + 中文消息\n    与AI进行MBTI主题对话（16型人格角色扮演）")
    
    if plugin_commands:
        help_text += "\n\n🎮 趣味功能\n" + "\n".join(plugin_commands)
    
    # 帮助系统说明
    help_text += """

🔧 帮助系统
• /help (或 /帮助)
    显示此帮助信息
• /help plugins (或 /help 列表)
    查看所有可用插件列表
• /help <插件名>
    查看指定插件的详细帮助

🔗 开发 & 部署
• 使用 "/help dev" 查看相关信息

💡 提示
• 所有指令均可使用 "/" 作为前缀
• 使用 "/help plugins" 探索更多功能

🙏 致谢
• 开发者: Sirilit(识启), AllayFocalors(玛画疼)
• QQ 群: "MBTI 一同启程"——的群友们对 bot 早期开发的支持和反馈~
"""
    
    return help_text

# 开发 & 部署信息（从主页分离）
DEV_HELP = """
🔗 开发 & 部署

这是一个开源项目，欢迎访问 GitHub 仓库：

• mbti统计插件 (nonebot2 插件)
  https://github.com/Siridelta/nonebot-plugin-mbtistats
  mbti统计功能为 nonebot2 插件的形式，可以加载到任何 NoneBot 2 机器人上使用哦~

• 机器人整体开发 & 部署仓库
  https://github.com/Siridelta/nonebot-plugin-mbtistats-devbot
  这是我们开发、调试 mbti 统计插件，以及部署本计数菌的仓库，包含了其他小工具和插件，可以直接 clone 和部署（如果想部署一个跟我一模一样的计数菌 bot 的话）

• 这两个仓库目前还在早期开发阶段，换句话说还没准备好正式开源发布x 但是如果你对这个项目感兴趣，欢迎提前关注和 star 哦～
""".strip()


def get_visible_plugins():
    """获取可见的插件列表（白名单机制）"""
    whitelist = help_config.help_visible_plugins if help_config else set()
    
    loaded = get_loaded_plugins()
    visible = list(loaded)
    visible.clear()  # 先转换后清空，em，只是为了让它有完整的类型提示（）

    # 白名单为空时显示所有插件（基础设施需要自己配置隐藏）
    if not whitelist:
        return loaded

    # 白名单不为空时，只显示白名单内的插件
    for plugin in loaded:
        # 跳过没有 metadata 的插件
        if not plugin.metadata:
            continue
        # 插件包名和 metadata.name 都可以作为匹配项
        if plugin.name not in whitelist and (plugin.metadata.name not in whitelist):
            continue
        visible.append(plugin)
    
    return visible


def format_plugin_list() -> str:
    """格式化插件列表为文本"""
    plugins = get_visible_plugins()
    
    if not plugins:
        return "暂无其他插件"
    
    lines = ["📦 已加载插件："]
    for plugin in plugins:
        meta = plugin.metadata
        name = meta.name or plugin.name
        desc = meta.description or "暂无描述"
        # 截断过长的描述
        if len(desc) > 50:
            desc = desc[:27] + "..."
        lines.append(f"  • {name} - {desc}")
    
    lines.append("")
    lines.append("使用 /help <插件名> 查看详细帮助")
    
    return "\n".join(lines)


@help_cmd.handle()
async def handle_help(bot: Bot, event: Event, matcher: Matcher):
    """
    处理 /help 命令
    无参数或参数为空时显示主页帮助
    参数为 plugins 时显示过滤后的插件列表
    参数为其他时查询具体插件帮助
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
        await matcher.send(get_home_help())
        return
    
    # 参数为 plugins/列表 -> 显示过滤后的插件列表
    if text in ["plugins", "列表"]:
        plugin_list = format_plugin_list()
        await matcher.send(plugin_list)
        return
    
    # 参数为 dev -> 显示开发 & 部署信息
    if text in ["dev"]:
        await matcher.send(DEV_HELP)
        return
    
    # 其他参数（可能是插件名）-> 查询具体插件
    plugin_name = text
    
    # 查找插件
    found = None
    for plugin in get_loaded_plugins():
        # 匹配插件包名或 metadata.name
        if plugin.name == plugin_name:
            found = plugin
            break
        if plugin.metadata and plugin.metadata.name == plugin_name:
            found = plugin
            break
    
    if found and found.metadata and found in get_visible_plugins():
        meta = found.metadata
        name = meta.name or found.name
        desc = meta.description or "暂无描述"
        usage = meta.usage or "暂无使用说明"
        
        help_text = f"「{name}」\n{desc}\n\n使用方法：\n{usage}"
        await matcher.send(help_text)
    else:
        await matcher.send(f"❓ 未找到插件「{plugin_name}」\n\n使用 /help plugins 查看可用插件列表")
