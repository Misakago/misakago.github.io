#!/usr/bin/env python3
"""
静态博客生成器
将 Markdown 文件转换为 HTML 静态网站
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
import base64
from typing import List, Dict

# 博客配置
SITE_TITLE = "Misaka's Tech Blog"
SITE_DESCRIPTION = "技术分享与实践记录"
SITE_AUTHOR = "Misaka"
GITHUB_URL = "https://github.com/Misakago"
SITE_URL = "https://misakago.github.io"

# 源目录和输出目录
SOURCE_DIR = Path(__file__).parent
OUTPUT_DIR = SOURCE_DIR / "site"
IMAGES_DIR = SOURCE_DIR / "images"

# HTML 模板
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {site_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: #2c3e50;
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        header h1 {{ margin: 0; font-size: 2rem; }}
        header p {{ opacity: 0.8; margin-top: 0.5rem; }}
        nav {{
            background: #34495e;
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        nav a {{
            color: #ecf0f1;
            text-decoration: none;
            padding: 0.5rem 1rem;
            margin: 0 0.5rem;
            border-radius: 4px;
            transition: background 0.3s;
        }}
        nav a:hover {{ background: #1abc9c; }}
        .article {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .article h1 {{ color: #2c3e50; margin-bottom: 1rem; font-size: 2rem; }}
        .article h2 {{ color: #34495e; margin: 2rem 0 1rem; font-size: 1.5rem; border-bottom: 2px solid #ecf0f1; padding-bottom: 0.5rem; }}
        .article h3 {{ color: #7f8c8d; margin: 1.5rem 0 0.5rem; font-size: 1.3rem; }}
        .article h4 {{ color: #95a5a6; margin: 1rem 0 0.5rem; font-size: 1.1rem; }}
        .article p {{ margin-bottom: 1rem; text-align: justify; }}
        .article ul, .article ol {{ margin-left: 2rem; margin-bottom: 1rem; }}
        .article li {{ margin-bottom: 0.5rem; }}
        .article code {{
            background: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.9em;
        }}
        .article pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 1.5rem;
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 1.5rem;
        }}
        .article pre code {{
            background: transparent;
            padding: 0;
            color: inherit;
        }}
        .article blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 1.5rem;
            margin: 1.5rem 0;
            color: #7f8c8d;
            font-style: italic;
        }}
        .article table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
        }}
        .article table th, .article table td {{
            border: 1px solid #ddd;
            padding: 0.75rem;
            text-align: left;
        }}
        .article table th {{ background: #34495e; color: white; }}
        .article table tr:nth-child(even) {{ background: #f8f9fa; }}
        .article img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin: 1.5rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .article a {{ color: #3498db; text-decoration: none; }}
        .article a:hover {{ text-decoration: underline; }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #ecf0f1;
        }}
        .index-item {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .index-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .index-item h2 {{ margin-bottom: 0.5rem; }}
        .index-item h2 a {{ color: #2c3e50; text-decoration: none; }}
        .index-item h2 a:hover {{ color: #3498db; }}
        .index-item p {{ color: #7f8c8d; }}
        .index-date {{ color: #95a5a6; font-size: 0.9rem; }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
            margin-top: 3rem;
        }}
        footer a {{ color: #3498db; text-decoration: none; }}
        .back-link {{ display: inline-block; margin-bottom: 1rem; color: #3498db; text-decoration: none; }}
        .tag {{ display: inline-block; background: #ecf0f1; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; margin-right: 0.5rem; }}
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .article {{ padding: 1.5rem; }}
            header h1 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{site_title}</h1>
            <p>{site_description}</p>
        </div>
    </header>
    <nav>
        <div class="container">
            <a href="{site_url}/">首页</a>
            <a href="{github_url}" target="_blank">GitHub</a>
        </div>
    </nav>
    <div class="container">
        {content}
    </div>
    <footer>
        <p>&copy; {year} {site_author}. Powered by <a href="https://pages.github.com/">GitHub Pages</a></p>
        <p><a href="{github_url}">{github_url}</a></p>
    </footer>
</body>
</html>
"""


def get_all_markdown_files() -> List[Path]:
    """获取所有markdown文件"""
    return sorted(SOURCE_DIR.glob("*.md"))


def extract_title(content: str) -> str:
    """从markdown内容中提取标题"""
    # 尝试提取第一个一级标题
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # 尝试提取文件名作为标题
    return "Untitled"


def extract_description(content: str) -> str:
    """提取文章描述（第一段）"""
    # 移除标题行
    lines = [line for line in content.split('\n') if not line.startswith('#')]
    # 找到第一个非空段落
    for line in lines:
        line = line.strip()
        if line and not line.startswith('!') and not line.startswith('|'):
            # 清理markdown语法
            desc = re.sub(r'[*_`#\[\]]', '', line)
            return desc[:100] + '...' if len(desc) > 100 else desc
    return ""


def markdown_to_html(content: str) -> str:
    """将markdown转换为HTML（简化版）"""
    lines = content.split('\n')
    html_lines = []
    in_code_block = False
    code_lang = ''
    code_content = []
    in_list = False

    for line in lines:
        # 代码块处理
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip() or 'text'
                code_content = []
            else:
                # 代码块结束
                newline = '\n'
                code_html = f'<pre><code class="language-{code_lang}">{newline.join(code_content)}</code></pre>'
                html_lines.append(code_html)
                in_code_block = False
            continue

        if in_code_block:
            # 转义HTML特殊字符
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            code_content.append(escaped)
            continue

        # 一级标题
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:].strip()}</h1>')
        # 二级标题
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:].strip()}</h2>')
        # 三级标题
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:].strip()}</h3>')
        # 四级标题
        elif line.startswith('#### '):
            html_lines.append(f'<h4>{line[5:].strip()}</h4>')
        # 引用
        elif line.startswith('> '):
            html_lines.append(f'<blockquote>{line[2:].strip()}</blockquote>')
        # 图片
        elif line.startswith('![') and '](' in line:
            alt_text = re.search(r'!\[(.*?)\]', line)
            url = re.search(r'\]\((.*?)\)', line)
            if alt_text and url:
                # 处理相对路径图片
                img_url = url.group(1)
                if img_url.startswith('images/'):
                    img_url = '/' + img_url
                html_lines.append(f'<img src="{img_url}" alt="{alt_text.group(1)}">')
        # 链接
        elif line.startswith('[') and '](' in line and not line.startswith('!['):
            text = re.search(r'\[(.*?)\]', line)
            url = re.search(r'\]\((.*?)\)', line)
            if text and url:
                html_lines.append(f'<p><a href="{url.group(1)}" target="_blank">{text.group(1)}</a></p>')
        # 无序列表
        elif line.startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{process_inline_markdown(line[2:].strip())}</li>')
        # 有序列表
        elif re.match(r'^\d+\.\s', line):
            if not in_list:
                html_lines.append('<ol>')
                in_list = True
            content = re.sub(r'^\d+\.\s', '', line)
            html_lines.append(f'<li>{process_inline_markdown(content.strip())}</li>')
        # 空行 - 结束列表
        elif not line.strip():
            if in_list:
                html_lines.append('</ul>' if html_lines[-1].startswith('<li>-') else '</ol>')
                in_list = False
            html_lines.append('<br>')
        # 表格
        elif '|' in line and line.strip():
            # 简单处理表格
            cells = [cell.strip() for cell in line.split('|')]
            cells = [c for c in cells if c]  # 移除空单元格
            if cells and not all(c.startswith('-') or c.startswith('---') for c in cells):
                if 'table' not in ''.join(html_lines[-5:] if html_lines else []):
                    html_lines.append('<table><thead><tr>')
                    tag = 'th'
                else:
                    html_lines.append('<tr>')
                    tag = 'td'
                for cell in cells:
                    html_lines.append(f'<{tag}>{process_inline_markdown(cell)}</{tag}>')
                html_lines.append('</tr>')
                if tag == 'th':
                    html_lines.append('</thead><tbody>')
        # 普通段落
        elif line.strip():
            if in_list:
                html_lines.append('</ul>' if '<li>-' in html_lines[-10:] else '</ol>')
                in_list = False
            html_lines.append(f'<p>{process_inline_markdown(line.strip())}</p>')

    return '\n'.join(html_lines)


def process_inline_markdown(text: str) -> str:
    """处理行内markdown"""
    # 粗体
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # 代码
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    # 链接
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', text)
    return text


def get_file_slug(filename: str) -> str:
    """从文件名生成URL友好的slug"""
    # 移除.md扩展名
    name = filename.replace('.md', '')
    # 转换为URL友好格式
    slug = re.sub(r'[^\w\u4e00-\u9fff\-]', '-', name)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug.lower() if slug.isascii() else slug


def generate_post(slug: str, content: str, title: str, date_str: str) -> str:
    """生成单篇文章HTML"""
    post_html = markdown_to_html(content)

    article_content = f"""
        <a href="/" class="back-link">← 返回首页</a>
        <article class="article">
            <h1>{title}</h1>
            <div class="meta">发布于 {date_str}</div>
            {post_html}
        </article>
    """

    return HTML_TEMPLATE.format(
        title=title,
        site_title=SITE_TITLE,
        site_description=SITE_DESCRIPTION,
        site_author=SITE_AUTHOR,
        github_url=GITHUB_URL,
        site_url=SITE_URL,
        year=datetime.now().year,
        content=article_content
    )


def generate_index(posts: List[Dict]) -> str:
    """生成首页HTML"""
    index_content = '<h1>最新文章</h1>\n\n'

    for post in reversed(posts):  # 最新的在前
        index_content += f"""
        <div class="index-item">
            <h2><a href="/{post['slug']}.html">{post['title']}</a></h2>
            <p>{post['description']}</p>
            <span class="index-date">{post['date']}</span>
        </div>
        """

    return HTML_TEMPLATE.format(
        title="首页",
        site_title=SITE_TITLE,
        site_description=SITE_DESCRIPTION,
        site_author=SITE_AUTHOR,
        github_url=GITHUB_URL,
        site_url=SITE_URL,
        year=datetime.now().year,
        content=index_content
    )


def build_site():
    """构建整个网站"""
    print(f"🔨 开始构建网站...")

    # 清理并创建输出目录
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # 复制图片目录
    images_output = OUTPUT_DIR / "images"
    if IMAGES_DIR.exists():
        shutil.copytree(IMAGES_DIR, images_output)
        print(f"📁 复制了 {len(list(IMAGES_DIR.glob('*')))} 个图片文件")

    # 获取所有markdown文件
    md_files = get_all_markdown_files()
    print(f"📝 找到 {len(md_files)} 篇文章")

    posts = []

    # 处理每篇文章
    for md_file in md_files:
        print(f"  - 处理: {md_file.name}")

        # 读取内容
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取信息
        title = extract_title(content)
        slug = get_file_slug(md_file.name)
        description = extract_description(content)

        # 获取文件修改时间作为发布日期
        mtime = md_file.stat().st_mtime
        date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

        posts.append({
            'title': title,
            'slug': slug,
            'description': description,
            'date': date,
            'file': md_file
        })

        # 生成文章页面
        post_html = generate_post(slug, content, title, date)
        post_file = OUTPUT_DIR / f"{slug}.html"
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(post_html)

    # 生成首页
    index_html = generate_index(posts)
    with open(OUTPUT_DIR / "index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"✅ 网站构建完成!")
    print(f"   - 生成了 {len(posts)} 篇文章")
    print(f"   - 输出目录: {OUTPUT_DIR}")


if __name__ == '__main__':
    build_site()
