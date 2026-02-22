from asyncio import sleep
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging
import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.console import Adapter as ConsoleAdapter
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from nonebot.log import logger, default_filter, default_format

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 生成日志文件名（按日期时间）
log_file = log_dir / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 配置文件处理器
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)

# 添加到 NoneBot 的日志记录器
logger.add(file_handler, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {name} | {message}")

print(f"日志文件已创建: {log_file.absolute()}")

# 初始化 NoneBot
nonebot.init()

# 注册 Adapters
driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)
driver.register_adapter(ConsoleAdapter)
# driver.register_adapter(OneBotV11Adapter)  # 暂时禁用 OneBot v11

# 加载插件
nonebot.load_from_toml("pyproject.toml")
nonebot.load_builtin_plugins("single_session")
logger.info("Loading plugins from plugins directory...")
nonebot.load_plugins("plugins")
logger.info("Plugins loaded!")

if __name__ == "__main__":
    nonebot.run()
