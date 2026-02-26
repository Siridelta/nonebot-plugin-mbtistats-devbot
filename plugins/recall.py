from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Bot,
    MessageSegment as OneBotMessageSegment,
    Message as OneBotMessage,
)
from nonebot.adapters.console import MessageEvent as ConsoleMessageEvent
from typing import List
import asyncio

__plugin_meta__ = PluginMetadata(
    name="recall",
    description="撤回机器人自己发送的消息",
    usage="""用法：
  /recall [数量]

示例：
  /recall     # 撤回最近 5 条（默认）
  /recall 10  # 撤回最近 10 条

限制：
  • 只能撤回机器人自己发送的消息
  • 受限于消息记录缓存，太久远的消息可能无法撤回
  • 仅支持 OneBot V11 协议（QQ 群聊）
  • 频繁撤回可能触发平台频率限制""",
    type="application",
)

recall_cmd = on_command("recall", priority=1, block=True)


async def get_bot_messages(bot: Bot, event: GroupMessageEvent, count: int, time_to: int) -> List[int]:
    """获取机器人最近发送的消息ID列表"""
    messages = []
    try:
        # 获取群消息历史
        history = await bot.get_group_msg_history(
            group_id=event.group_id,
            count=100  # 获取最近100条消息
        )
        
        # 筛选出机器人发送的消息
        for msg in reversed(history['messages']):
            if int(msg.get("user_id")) == int(bot.self_id) and msg["time"] <= time_to:
                msg_id = msg.get("message_id")
                if msg_id is not None:
                    messages.append(int(msg_id))
                if len(messages) >= count:
                    break
    except Exception as e:
        print(f"获取消息历史失败: {e}")
    
    return messages


async def recall_messages(bot: Bot, message_ids: List[int]) -> int:
    """撤回消息列表，返回成功撤回的数量"""
    success_count = 0
    for msg_id in message_ids:
        try:
            await bot.delete_msg(message_id=msg_id)
            success_count += 1
            # 避免触发频率限制
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"撤回消息 {msg_id} 失败: {e}")
    return success_count


@recall_cmd.handle()
async def handle_recall(bot: Bot, event: MessageEvent, message: Message = CommandArg()):
    # 只在群聊中支持撤回
    if not isinstance(event, GroupMessageEvent):
        if isinstance(event, ConsoleMessageEvent):
            await recall_cmd.finish("此功能仅支持 OneBot v11 群聊模式")
        else:
            await recall_cmd.finish("此功能仅支持群聊")
    
    text = message.extract_plain_text().strip()
    
    if not text:
        await recall_cmd.finish("请输入要撤回的消息数量\n示例: /recall 5")
    
    # 解析数量
    try:
        count = int(text)
    except ValueError:
        await recall_cmd.finish("请输入有效的数字\n示例: /recall 5")
    
    # 验证数量
    if count <= 0:
        await recall_cmd.finish("数量必须大于0")
    
    if count > 50:
        await recall_cmd.finish("一次最多撤回50条消息")
    
    # 获取机器人消息
    user_id = event.get_user_id()
    user_mention = OneBotMessageSegment.at(user_id)
    
    await recall_cmd.send(OneBotMessage([
            user_mention, 
            OneBotMessageSegment.text(f" 正在撤回最近 {count} 条机器人消息...")
        ]))
    
    bot_messages = await get_bot_messages(bot, event, count, event.time - 1)  # 防止刚才发送的提示消息被撤回
    
    if not bot_messages:
        await recall_cmd.finish(OneBotMessage([
                user_mention, 
                OneBotMessageSegment.text(" 未找到可撤回的机器人消息")
            ]))
    
    # 撤回消息
    success_count = await recall_messages(bot, bot_messages)
    
    # 发送结果
    if success_count == count:
        await recall_cmd.send(OneBotMessage([
                user_mention, 
                OneBotMessageSegment.text(f" ✅ 成功撤回 {success_count} 条消息")
            ]))
    else:
        await recall_cmd.send(OneBotMessage([
                user_mention, 
                OneBotMessageSegment.text(f" ⚠️ 成功撤回 {success_count}/{len(bot_messages)} 条消息")
            ]))
