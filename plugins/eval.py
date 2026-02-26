from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.exception import FinishedException

__plugin_meta__ = PluginMetadata(
    name="eval",
    description="执行 Python 表达式（仅限开发环境使用）",
    usage="""⚠️ 警告：此命令执行任意 Python 代码，仅限开发调试使用，生产环境请禁用！

用法：
  /eval <Python表达式>

示例：
  /eval 1+1
  /eval len([1,2,3])
  /eval str(123)

安全限制：
  • 无法访问内置函数（__builtins__ 已禁用）
  • 仅支持纯表达式计算""",
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
        await eval_cmd.finish(f"{result}")
    except FinishedException:
        pass
    except Exception as e:
        await eval_cmd.finish(f"执行错误: {e}")
