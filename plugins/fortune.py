import hashlib
import random
from datetime import datetime
from typing import Optional, Tuple, List

from nonebot import on_command, logger, get_driver
from nonebot.plugin import PluginMetadata, get_plugin_config
from nonebot.adapters import Bot, Event, Message
from nonebot.params import CommandArg
from pydantic import BaseModel, Field

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai 库未安装，运势润色功能将不可用")

from nonebot import require
require("nonebot_plugin_mbtistats")
from nonebot_plugin_mbtistats.analyze import parse_mbti_from_text


__plugin_meta__ = PluginMetadata(
    name="fortune",
    description="MBTI运势测试插件 - 基于算法生成积极向上的运势",
    usage="""用法：
  /运势 [MBTI类型] [出生日期(可选)]
  /今日运势 [MBTI类型]

示例：
  /运势 INFP
  /运势 INFP 1999-05-20
  /运势 INFJ 2000-01-01

说明：
  • 运势基于算法生成，确保积极向上
  • 每日运势固定，同一用户同一天结果一致
  • 支持16种MBTI人格类型
  • 可选填出生日期以获得更个性化结果""",
    type="application",
)


class FortuneConfig(BaseModel):
    """运势插件配置类"""
    
    ai_enabled: bool = Field(
        default=True, 
        description="AI润色功能开关"
    )
    ai_api_key: str = Field(
        default="", 
        description="LLM API密钥"
    )
    ai_base_url: str = Field(
        default="", 
        description="API基础URL"
    )
    ai_model: str = Field(
        default="ZP-glm-4.5-flash", 
        description="模型名称"
    )


# 获取插件配置
plugin_config = get_plugin_config(FortuneConfig)

# 运势维度定义
FORTUNE_DIMENSIONS = [
    ("综合运势", "⭐", 85, 100),
    ("爱情运势", "💕", 80, 100),
    ("事业运势", "💼", 80, 100),
    ("财运", "💰", 75, 100),
    ("健康运势", "🌟", 80, 100),
    ("人际关系", "🤝", 80, 100),
]

# MBTI 类型描述
MBTI_DESCRIPTIONS = {
    "INTJ": "战略家",
    "INTP": "逻辑学家",
    "ENTJ": "指挥官",
    "ENTP": "辩论家",
    "INFJ": "提倡者",
    "INFP": "调停者",
    "ENFJ": "主人公",
    "ENFP": "竞选者",
    "ISTJ": "物流师",
    "ISFJ": "守卫者",
    "ESTJ": "总经理",
    "ESFJ": "执政官",
    "ISTP": "鉴赏家",
    "ISFP": "探险家",
    "ESTP": "企业家",
    "ESFP": "表演者",
}

# 幸运元素池
LUCKY_ELEMENTS = {
    "colors": ["天蓝色", "薄荷绿", "暖橙色", "薰衣草紫", "珊瑚粉", "金色", "翡翠绿", "玫瑰红", "珍珠白", "星空蓝"],
    "numbers": ["3", "7", "8", "9", "12", "16", "21", "28", "33", "88"],
    "directions": ["东方", "南方", "西方", "北方", "东南", "东北", "西南", "西北"],
    "items": ["水晶", "笔记本", "咖啡", "绿植", "音乐", "书籍", "香薰", "手链", "钥匙扣", "明信片"],
    "activities": ["散步", "冥想", "写日记", "与朋友聊天", "听音乐", "阅读", "整理房间", "尝试新事物", "帮助他人", "享受美食"],
}

# 积极建议池
POSITIVE_ADVICE = [
    "今天适合尝试新事物，勇敢迈出第一步！",
    "保持乐观心态，好运会眷顾积极的人～",
    "相信自己的直觉，你比想象中更有力量！",
    "今天适合表达爱意，把温暖传递给身边的人～",
    "专注当下，美好的事情正在发生！",
    "保持微笑，你的能量会感染周围的人！",
    "今天适合制定计划，为未来打下坚实基础～",
    "相信自己的选择，每一步都是最好的安排！",
    "今天适合放松身心，给自己一些独处时光～",
    "保持好奇心，世界会为你打开新的大门！",
    "今天适合社交，可能会遇到志同道合的朋友～",
    "相信自己的价值，你值得所有美好的事物！",
    "今天适合学习新技能，成长永无止境～",
    "保持感恩的心态，幸福就在身边！",
    "今天适合整理思绪，清晰的头脑带来好运～",
    "相信直觉，你的内心知道正确的方向！",
]

# MBTI 专属建议
MBTI_SPECIFIC_ADVICE = {
    "INTJ": ["发挥你的战略思维，今天适合规划长远目标", "相信你的洞察力，你看到的比别人更远"],
    "INTP": ["发挥你的好奇心，今天适合探索新领域", "相信你的逻辑分析，真理越辩越明"],
    "ENTJ": ["发挥你的领导力，今天适合带领团队前进", "相信你的决断力，果断带来成功"],
    "ENTP": ["发挥你的创造力，今天适合头脑风暴", "相信你的机智，灵活应对一切挑战"],
    "INFJ": ["发挥你的同理心，今天适合深度交流", "相信你的直觉，内在智慧指引方向"],
    "INFP": ["发挥你的想象力，今天适合创作表达", "相信你的价值观，真诚是最美的力量"],
    "ENFJ": ["发挥你的感染力，今天适合激励他人", "相信你的魅力，温暖能改变世界"],
    "ENFP": ["发挥你的热情，今天适合追逐梦想", "相信你的可能性，世界充满惊喜"],
    "ISTJ": ["发挥你的责任心，今天适合完成重要任务", "相信你的可靠性，踏实带来安心"],
    "ISFJ": ["发挥你的细心，今天适合照顾身边的人", "相信你的奉献精神，温柔自有力量"],
    "ESTJ": ["发挥你的组织能力，今天适合统筹规划", "相信你的执行力，行动创造结果"],
    "ESFJ": ["发挥你的社交能力，今天适合联络感情", "相信你的体贴，关怀温暖人心"],
    "ISTP": ["发挥你的动手能力，今天适合实践探索", "相信你的冷静，沉稳应对变化"],
    "ISFP": ["发挥你的艺术感，今天适合欣赏美好", "相信你的敏感，细腻是独特天赋"],
    "ESTP": ["发挥你的行动力，今天适合把握机会", "相信你的直觉，活在当下最精彩"],
    "ESFP": ["发挥你的表演力，今天适合展现自我", "相信你的热情，快乐会传染"],
}


def validate_config() -> bool:
    """验证AI配置是否有效"""
    if not plugin_config.ai_api_key:
        logger.debug("AI_API_KEY 未配置，运势润色功能将使用本地模板")
        return False
    
    if not plugin_config.ai_base_url:
        logger.debug("AI_BASE_URL 未配置，运势润色功能将使用本地模板")
        return False
    
    if not OPENAI_AVAILABLE:
        logger.debug("openai 库未安装，运势润色功能将使用本地模板")
        return False
    
    return True


AI_ENABLED = plugin_config.ai_enabled and validate_config()


def get_seed(user_id: str, mbti_type: str, date_str: str) -> int:
    """生成基于用户ID、MBTI类型和日期的随机种子，确保同一天结果一致"""
    seed_str = f"{user_id}:{mbti_type}:{date_str}"
    return int(hashlib.md5(seed_str.encode()).hexdigest(), 16)


def generate_fortune_scores(seed: int) -> List[Tuple[str, str, int]]:
    """生成运势分数，确保高分为主"""
    rng = random.Random(seed)
    scores = []
    for dimension, emoji, min_score, max_score in FORTUNE_DIMENSIONS:
        # 加权随机，偏向高分
        score = rng.randint(min_score, max_score)
        scores.append((dimension, emoji, score))
    return scores


def get_lucky_elements(seed: int) -> dict:
    """获取今日幸运元素"""
    rng = random.Random(seed)
    return {
        "color": rng.choice(LUCKY_ELEMENTS["colors"]),
        "number": rng.choice(LUCKY_ELEMENTS["numbers"]),
        "direction": rng.choice(LUCKY_ELEMENTS["directions"]),
        "item": rng.choice(LUCKY_ELEMENTS["items"]),
        "activity": rng.choice(LUCKY_ELEMENTS["activities"]),
    }


def get_advice(seed: int, mbti_type: str) -> Tuple[str, str]:
    """获取今日建议"""
    rng = random.Random(seed)
    general_advice = rng.choice(POSITIVE_ADVICE)
    mbti_advice = rng.choice(MBTI_SPECIFIC_ADVICE.get(mbti_type, ["保持积极心态，好运自然来～"]))
    return general_advice, mbti_advice


def generate_fortune_content(
    mbti_type: str,
    user_id: str,
    date_str: str,
    user_name: str = ""
) -> str:
    """生成本地运势内容（不使用AI）"""
    seed = get_seed(user_id, mbti_type, date_str)
    rng = random.Random(seed)
    
    # 获取数据
    scores = generate_fortune_scores(seed)
    lucky = get_lucky_elements(seed)
    general_advice, mbti_advice = get_advice(seed, mbti_type)
    
    # 计算综合评分
    avg_score = sum(score for _, _, score in scores) // len(scores)
    
    # 获取MBTI描述
    mbti_desc = MBTI_DESCRIPTIONS.get(mbti_type, "探索者")
    
    # 生成运势等级
    if avg_score >= 95:
        fortune_level = "⭐⭐⭐⭐⭐ 超级幸运"
        level_emoji = "🌟🌟🌟"
    elif avg_score >= 90:
        fortune_level = "⭐⭐⭐⭐⭐ 大吉"
        level_emoji = "✨✨✨"
    elif avg_score >= 85:
        fortune_level = "⭐⭐⭐⭐ 吉"
        level_emoji = "✨✨"
    else:
        fortune_level = "⭐⭐⭐ 平吉"
        level_emoji = "✨"
    
    # 构建运势文本
    greeting = f"你好呀{user_name}～" if user_name else "你好呀～"
    
    content = f"""{greeting} 
今天是 {date_str}，{mbti_type}（{mbti_desc}）的运势如下：

{level_emoji} {fortune_level} {level_emoji}
综合评分：{avg_score}/100

📊 各项运势
"""
    
    for dimension, emoji, score in scores:
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        content += f"{emoji} {dimension}: {bar} {score}分\n"
    
    content += f"""
🍀 今日幸运元素
幸运色：{lucky['color']}
幸运数字：{lucky['number']}
幸运方位：{lucky['direction']}
幸运物品：{lucky['item']}
宜：{lucky['activity']}

💡 今日建议
{mbti_advice}
{general_advice}

祝你度过美好的一天～🌈
"""
    
    return content


async def polish_fortune_with_ai(
    base_content: str,
    mbti_type: str,
    scores: List[Tuple[str, str, int]],
    lucky: dict,
    avg_score: int
) -> Optional[str]:
    """使用AI润色运势文本"""
    if not AI_ENABLED:
        return None
    
    try:
        client = openai.OpenAI(
            api_key=plugin_config.ai_api_key,
            base_url=plugin_config.ai_base_url
        )
        
        # 构建润色提示词
        polish_prompt = f"""你是一位温暖积极的运势解读师。请基于以下运势数据，生成一段优美、温暖、积极向上的运势解读。

要求：
1. 保持积极向上的基调，避免任何负面表述
2. 语言优美流畅，富有感染力
3. 结合MBTI人格特点给出个性化建议
4. 适当使用emoji增加亲和力
5. 不使用Markdown格式（如**、#等）
6. 总字数控制在300-400字

MBTI类型：{mbti_type}
综合评分：{avg_score}/100
各项运势：{scores}
幸运元素：{lucky}

请直接输出润色后的运势文本，不要解释。"""

        response = client.chat.completions.create(
            model=plugin_config.ai_model,
            messages=[
                {"role": "system", "content": "你是一位温暖积极的运势解读师，擅长用优美的语言传递正能量。"},
                {"role": "user", "content": polish_prompt}
            ],
            temperature=0.7,
            max_tokens=600,
        )
        
        polished_text = response.choices[0].message.content.strip()
        logger.info(f"运势AI润色成功，长度: {len(polished_text)} 字符")
        return polished_text
        
    except Exception as e:
        logger.error(f"运势AI润色失败: {e}")
        return None


# 定义命令
fortune_cmd = on_command("运势", aliases={"今日运势", "测运势"}, priority=10, block=True)


@fortune_cmd.handle()
async def handle_fortune(bot: Bot, event: Event, args: Message = CommandArg()):
    """处理运势命令"""
    text = args.extract_plain_text().strip()
    user_id = event.get_user_id()
    
    # 获取用户名
    user_name = ""
    try:
        if hasattr(event, 'sender') and event.sender:
            user_name = getattr(event.sender, 'nickname', '') or getattr(event.sender, 'card', '')
    except:
        pass
    
    # 解析参数
    parts = text.split()
    mbti_type = None
    fuzzy_type = False
    birth_date = None
    
    for part in parts:
        part_upper = part.upper()
        if part_upper in MBTI_DESCRIPTIONS:
            mbti_type = part_upper
        # 尝试解析日期格式 YYYY-MM-DD 或 YYYY/MM/DD
        elif '-' in part or '/' in part:
            try:
                # 简单验证日期格式
                date_clean = part.replace('/', '-')
                datetime.strptime(date_clean, "%Y-%m-%d")
                birth_date = date_clean
            except ValueError:
                pass
    
    # 如果没有提供MBTI类型，尝试从群名片/昵称中识别
    if not mbti_type:
        try:
            if hasattr(event, 'sender') and event.sender:
                nickname = getattr(event.sender, 'card', '') or getattr(event.sender, 'nickname', '')
                mbti_data = parse_mbti_from_text(nickname)
                if mbti_data:
                    mbti_type = (
                        ("E" if mbti_data["EI"]["E"] else "I")
                        + ("S" if mbti_data["SN"]["S"] else "N")
                        + ("T" if mbti_data["TF"]["T"] else "F")
                        + ("J" if mbti_data["JP"]["J"] else "P")
                    )
                    fuzzy_type = (
                        (mbti_data["EI"]["E"] and mbti_data["EI"]["I"])
                        or (mbti_data["SN"]["S"] and mbti_data["SN"]["N"])
                        or (mbti_data["TF"]["T"] and mbti_data["TF"]["F"])
                        or (mbti_data["JP"]["J"] and mbti_data["JP"]["P"])
                    )
        except:
            pass
    
    if not mbti_type:
        await fortune_cmd.finish(
            "请提供你的MBTI类型～\n"
            "用法：/运势 INFP\n"
            "或：/运势 INFP 1999-05-20\n"
            "也可以把MBTI类型放在群名片里，我会自动识别！"
        )
        return
    
    if fuzzy_type:
        await fortune_cmd.finish(
            "哎呀，你的MBTI类型是模糊类型，我不太好进行运势测算呐......\n"
            "请提供你的MBTI类型～\n"
            "用法：/运势 INFP\n"
            "或：/运势 INFP 1999-05-20\n"
            "也可以把MBTI类型放在群名片里，我会自动识别！"
        )
        return

    # 获取今日日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 如果提供了出生日期，用它作为额外种子因子
    date_seed = birth_date if birth_date else today
    
    await fortune_cmd.send(f"正在为 {mbti_type} 测算今日运势...🔮")
    
    # 生成基础运势内容
    base_content = generate_fortune_content(mbti_type, user_id, date_seed, user_name)
    
    # 尝试AI润色
    if AI_ENABLED:
        seed = get_seed(user_id, mbti_type, date_seed)
        scores = generate_fortune_scores(seed)
        lucky = get_lucky_elements(seed)
        avg_score = sum(score for _, _, score in scores) // len(scores)
        
        polished = await polish_fortune_with_ai(base_content, mbti_type, scores, lucky, avg_score)
        if polished:
            # 在AI润色结果前加上运势数据
            header = f"🌟 {mbti_type} 今日运势 🌟\n日期：{today}\n"
            if birth_date:
                header += f"参考生日：{birth_date}\n"
            header += "\n"
            await fortune_cmd.finish(header + polished)
            return
    
    # 使用本地生成的运势
    await fortune_cmd.finish(base_content)
