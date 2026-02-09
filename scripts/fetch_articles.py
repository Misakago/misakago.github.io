#!/usr/bin/env python3
"""
文章处理脚本
将 Markdown 文件复制到 public/articles 目录，并生成索引文件
"""

import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 配置
SOURCE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = SOURCE_DIR / "public" / "articles"
IMAGES_OUTPUT_DIR = SOURCE_DIR / "public" / "images"
IMAGES_SOURCE_DIR = SOURCE_DIR / "images"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_all_markdown_files() -> List[Path]:
    """获取所有markdown文件（排除README）"""
    return sorted([
        f for f in SOURCE_DIR.glob("*.md")
        if f.name != "README.md"
    ])


def extract_title(content: str, filename: str) -> str:
    """从markdown内容中提取标题

    支持以下格式:
    - # 标题
    - 1. # 标题 (有序列表后跟标题)
    """
    lines = content.split('\n')

    for line in lines:
        # 标准格式: # 标题
        match = re.match(r'^#\s+(.+)$', line.strip())
        if match:
            return match.group(1).strip()

        # 列表格式: 1. # 标题
        match = re.match(r'^\d+\.\s*#\s+(.+)$', line.strip())
        if match:
            return match.group(1).strip()

    # 如果没有找到标题，使用文件名
    return filename.replace('.md', '')


def extract_description(content: str) -> str:
    """提取文章描述（第一段有效内容）"""
    lines = content.split('\n')

    # 跳过标题行
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not (stripped.startswith('#') or
                            re.match(r'^\d+\.\s*#', stripped)):
            start_idx = i
            break

    # 找到第一个非空段落
    for line in lines[start_idx:]:
        stripped = line.strip()
        if stripped and not stripped.startswith('!') and '|' not in stripped:
            # 清理markdown语法
            desc = re.sub(r'[*_`\[\]]', '', stripped)
            # 移除列表标记
            desc = re.sub(r'^[-\*]\s*', '', desc)
            desc = re.sub(r'^\d+\.\s*', '', desc)
            desc = desc.strip()
            if desc:
                return desc[:150] + '...' if len(desc) > 150 else desc

    return ""


def get_file_slug(filename: str) -> str:
    """从文件名生成URL友好的slug"""
    # 移除.md扩展名
    name = filename.replace('.md', '')
    # 移除特殊字符，保留中文、字母、数字和连字符
    slug = re.sub(r'[^\w\u4e00-\u9fff\-]', '-', name)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def process_markdown_images(content: str, slug: str) -> str:
    """处理 Markdown 中的图片路径

    将 images/xxx.png 转换为 /images/xxx.png
    """
    # 替换图片路径
    content = re.sub(
        r'!\[(.*?)\]\(images/([^)]+)\)',
        r'![\1](/images/\2)',
        content
    )
    return content


def copy_images():
    """复制图片到 public 目录"""
    if not IMAGES_SOURCE_DIR.exists():
        print(f"  ℹ️  图片源目录不存在: {IMAGES_SOURCE_DIR}")
        return

    # 清理并重建目标目录
    if IMAGES_OUTPUT_DIR.exists():
        shutil.rmtree(IMAGES_OUTPUT_DIR)
    IMAGES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 复制所有图片
    image_files = list(IMAGES_SOURCE_DIR.glob('*'))
    image_count = 0

    for img in image_files:
        if img.is_file():
            shutil.copy2(img, IMAGES_OUTPUT_DIR / img.name)
            image_count += 1

    print(f"  📷 复制了 {image_count} 个图片文件")


def build_articles():
    """构建文章索引和内容"""
    print(f"🔨 开始处理文章...")

    # 清理输出目录
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("*.md"):
            f.unlink()
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 复制图片
    copy_images()

    # 获取所有markdown文件
    md_files = get_all_markdown_files()
    print(f"  📝 找到 {len(md_files)} 篇文章")

    articles = []

    # 处理每篇文章
    for md_file in md_files:
        print(f"    - {md_file.name}")

        # 读取内容
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取信息
        title = extract_title(content, md_file.name)
        slug = get_file_slug(md_file.name)
        description = extract_description(content)

        # 获取文件修改时间作为发布日期
        mtime = md_file.stat().st_mtime
        date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

        articles.append({
            'title': title,
            'slug': slug,
            'description': description,
            'date': date,
            'filename': md_file.name
        })

        # 处理图片路径
        processed_content = process_markdown_images(content, slug)

        # 写入处理后的 markdown 文件
        output_file = OUTPUT_DIR / f"{slug}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)

    # 按日期排序（最新的在前）
    articles.sort(key=lambda x: x['date'], reverse=True)

    # 生成索引文件
    index_file = OUTPUT_DIR / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 文章处理完成!")
    print(f"   - 处理了 {len(articles)} 篇文章")
    print(f"   - 输出目录: {OUTPUT_DIR}")


if __name__ == '__main__':
    build_articles()
