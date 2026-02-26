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
help_cmd = on_command("help", aliases={"帮助"}, rule=to_me(), priority=1, block=True)

# 主页帮助文本（突出 MBTI 统计 - 机器人核心身份）
HOME_HELP = """
你好呀，我是 MBTI 计数菌～
我是一位专注于 MBTI 人格类型统计的机器人，可以自动识别群名片/昵称中的 MBTI 类型，生成统计图表。


📊 核心功能

/mbti
  统计当前群的 MBTI 类型分布和特质维度分布，生成统计图
  
支持的类型格式：
  • 标准型：INTP、enfp（全大写/全小写）
  • 模糊型：INXP、exxp（用 X/x 代替不确定字母）
  • 扩展型：INTP-T、INTP(5w4)（识别其中的 MBTI 代码）
  • OPS 型：Te/Se、Ni/Fe（识别优势功能代码）

需要群友在群名片或 QQ 昵称中主动标注自己的 MBTI 类型才能被统计到哦～


🔧 其他功能

/help (或 /帮助)
  显示此帮助信息，需要 @bot。

/help plugins
  查看所有可用插件列表

/help <插件名>
  查看指定插件的详细帮助


💡 提示

• 所有指令均可使用 "/" 作为前缀
• 使用 "/help plugins" 探索更多功能
""".strip()


def get_visible_plugins():
    """获取可见的插件列表（白名单机制）"""
    whitelist = help_config.help_visible_plugins if help_config else set()
    
    visible = []
    for plugin in get_loaded_plugins():
        # 白名单为空时显示所有插件（基础设施需要自己配置隐藏）
        # 白名单不为空时，只显示白名单内的插件
        if whitelist and plugin.name not in whitelist:
            continue
        # 跳过没有 metadata 的插件
        if not plugin.metadata:
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
        if len(desc) > 30:
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
        await matcher.send(HOME_HELP)
        return
    
    # 参数为 plugins/all/列表 -> 显示过滤后的插件列表
    if text in ["plugins", "all", "列表", "plugin", "list"]:
        plugin_list = format_plugin_list()
        await matcher.send(plugin_list)
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
    
    if found and found.metadata and found.name in get_visible_plugins():
        meta = found.metadata
        name = meta.name or found.name
        desc = meta.description or "暂无描述"
        usage = meta.usage or "暂无使用说明"
        
        help_text = f"「{name}」\n{desc}\n\n使用方法：\n{usage}"
        await matcher.send(help_text)
    else:
        await matcher.send(f"❓ 未找到插件「{plugin_name}」\n\n使用 /help plugins 查看可用插件列表")
