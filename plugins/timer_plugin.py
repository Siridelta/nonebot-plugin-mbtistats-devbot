from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
import asyncio

__plugin_meta__ = PluginMetadata(
    name="timer",
    description="倒计时提醒插件",
    usage="/timer [时长] [提醒内容]",
)

timer_cmd = on_command("timer", priority=1, block=True)


@timer_cmd.handle()
async def handle_timer(message: Message = CommandArg()):
    text = message.extract_plain_text().strip()
    
    if not text:
        await timer_cmd.finish("请输入倒计时时间，如: /timer 30s 测试")
    
    parts = text.split(maxsplit=1)
    time_str = parts[0]
    reminder = parts[1] if len(parts) > 1 else "时间到！"
    
    # 简单解析
    seconds = 0
    import re
    match = re.match(r'(\d+)([smh])', time_str.lower())
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if unit == 's':
            seconds = num
        elif unit == 'm':
            seconds = num * 60
        elif unit == 'h':
            seconds = num * 3600
    
    if seconds <= 0 or seconds > 86400:
        await timer_cmd.finish("时间格式错误，支持: 30s, 5m, 1h")
    
    await timer_cmd.send(f"已设置 {seconds} 秒后提醒: {reminder}")
    
    await asyncio.sleep(seconds)
    await timer_cmd.send(f"⏰ {reminder}")
