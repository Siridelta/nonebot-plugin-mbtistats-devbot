#!/usr/bin/env python3
"""
数据迁移脚本：从旧目录结构迁移到新目录结构

旧结构:
  data/v1/cache-charts/{group_id}/mbti-stats.json      -> 数据文件
  data/v1/cache-charts/{group_id}/mbti-stats.png       -> 缓存图片
  data/v1/auto_stats_disabled.txt                      -> 黑名单

新结构:
  data/mbtistats/data/v1/{group_id}/stats-data.json
  data/mbtistats/cache/v1/{group_id}/mbti-stats-pic-{timestamp}.png
  data/mbtistats/auto_stats_disabled.txt

使用方法:
  1. 停止 Bot
  2. 备份数据目录
  3. 运行: python scripts/migrate_data_v1.py
  4. 检查迁移结果
  5. 启动 Bot
"""

import sys
import shutil
import time
from pathlib import Path

# 默认路径（相对脚本位置）
OLD_DATA_DIR = Path("data/v1/cache-charts")
OLD_DISABLED_FILE = Path("data/v1/auto_stats_disabled.txt")
NEW_DATA_ROOT = Path("data/mbtistats")
NEW_DATA_DIR = NEW_DATA_ROOT / "data" / "v1"
NEW_CACHE_DIR = NEW_DATA_ROOT / "cache" / "v1"
NEW_DISABLED_FILE = NEW_DATA_ROOT / "auto_stats_disabled.txt"


def migrate_group_data(group_dir: Path) -> bool:
    """迁移单个群的数据"""
    group_id = group_dir.name
    
    # 新路径
    new_data_dir = NEW_DATA_DIR / group_id
    new_cache_dir = NEW_CACHE_DIR / group_id
    
    new_data_dir.mkdir(parents=True, exist_ok=True)
    new_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 迁移 JSON 数据文件
    old_json = group_dir / "mbti-stats.json"
    new_json = new_data_dir / "stats-data.json"
    
    if old_json.exists():
        shutil.copy2(old_json, new_json)
        print(f"  [数据] {old_json} -> {new_json}")
    
    # 迁移 PNG 缓存文件（带时间戳重命名）
    old_png = group_dir / "mbti-stats.png"
    if old_png.exists():
        # 使用文件修改时间作为时间戳
        mtime = old_png.stat().st_mtime
        timestamp = int(mtime * 1000)
        new_png = new_cache_dir / f"mbti-stats-pic-{timestamp}.png"
        shutil.copy2(old_png, new_png)
        print(f"  [缓存] {old_png} -> {new_png}")
    
    return True


def migrate():
    """执行迁移"""
    print("=" * 60)
    print("MBTI Stats 数据迁移脚本")
    print("=" * 60)
    print()
    
    # 检查旧数据是否存在
    if not OLD_DATA_DIR.exists():
        print(f"错误: 旧数据目录不存在: {OLD_DATA_DIR}")
        print("请确认当前目录是否正确，或数据已经迁移过。")
        return False
    
    # 确认
    print("将执行以下迁移:")
    print(f"  从: {OLD_DATA_DIR}")
    print(f"  到: {NEW_DATA_ROOT}")
    print()
    
    response = input("确认开始迁移? [y/N]: ")
    if response.lower() != 'y':
        print("已取消")
        return False
    
    print()
    print("开始迁移...")
    print("-" * 60)
    
    # 创建新目录结构
    NEW_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    
    # 迁移黑名单文件
    if OLD_DISABLED_FILE.exists():
        shutil.copy2(OLD_DISABLED_FILE, NEW_DISABLED_FILE)
        print(f"[配置] {OLD_DISABLED_FILE} -> {NEW_DISABLED_FILE}")
    else:
        # 创建空的黑名单文件
        NEW_DISABLED_FILE.touch()
        print(f"[配置] 创建新的黑名单文件: {NEW_DISABLED_FILE}")
    
    # 迁移每个群的数据
    group_count = 0
    for group_dir in OLD_DATA_DIR.iterdir():
        if group_dir.is_dir():
            print(f"\n群 {group_dir.name}:")
            if migrate_group_data(group_dir):
                group_count += 1
    
    print()
    print("-" * 60)
    print(f"迁移完成! 共迁移 {group_count} 个群的数据")
    print()
    print("新目录结构:")
    print(f"  {NEW_DATA_ROOT}/")
    print(f"  ├── auto_stats_disabled.txt")
    print(f"  ├── data/v1/{{group_id}}/stats-data.json")
    print(f"  └── cache/v1/{{group_id}}/mbti-stats-pic-{{timestamp}}.png")
    print()
    print("建议:")
    print("  1. 检查新目录中的数据是否正确")
    print("  2. 确认无误后，可以删除旧目录: data/v1/")
    print("  3. 更新 Bot 配置，使用新的数据路径")
    
    return True


def dry_run():
    """预览迁移（不实际执行）"""
    print("=" * 60)
    print("MBTI Stats 数据迁移预览 (Dry Run)")
    print("=" * 60)
    print()
    
    if not OLD_DATA_DIR.exists():
        print(f"旧数据目录不存在: {OLD_DATA_DIR}")
        return
    
    print("将执行以下操作:")
    print()
    
    # 黑名单
    if OLD_DISABLED_FILE.exists():
        print(f"[配置] 迁移: {OLD_DISABLED_FILE} -> {NEW_DISABLED_FILE}")
    
    # 群数据
    for group_dir in OLD_DATA_DIR.iterdir():
        if group_dir.is_dir():
            group_id = group_dir.name
            old_json = group_dir / "mbti-stats.json"
            old_png = group_dir / "mbti-stats.png"
            
            print(f"\n群 {group_id}:")
            if old_json.exists():
                print(f"  [数据] {old_json}")
                print(f"       -> {NEW_DATA_DIR / group_id / 'stats-data.json'}")
            if old_png.exists():
                mtime = old_png.stat().st_mtime
                timestamp = int(mtime * 1000)
                print(f"  [缓存] {old_png}")
                print(f"       -> {NEW_CACHE_DIR / group_id / f'mbti-stats-pic-{timestamp}.png'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run()
    else:
        success = migrate()
        sys.exit(0 if success else 1)
