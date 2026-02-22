from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="eval",
    description="执行 Python 表达式（仅限开发环境）",
    usage="/eval [expression]",
    type="application",
)

eval_cmd = on_command("eval", priority=1, block=True)


@eval_cmd.handle()
async def handle_eval(message: Message = CommandArg()):
    text = message.extract_plain_text().strip()
    
    if not text:
        await eval_cmd.finish("请输入要执行的表达式，例如：/eval 1+1")
    
    try:
        result = eval(text, {"__builtins__": {}}, {})
        await eval_cmd.finish(f"结果: {result}")
    except Exception as e:
        await eval_cmd.finish(f"执行错误: {e}")
