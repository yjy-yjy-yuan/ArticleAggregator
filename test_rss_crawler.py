"""
RSS爬虫测试文件
作用：从 rss_sources_for_ai_students.json 读取RSS源并抓取文章
"""

import feedparser
import json
import sqlite3
from datetime import datetime
import time

# ============= 配置 =============
RSS_CONFIG_FILE = "rss_sources_for_ai_students.json"
DATABASE_FILE = "data/ai_student_articles.db"
MAX_ARTICLES_PER_SOURCE = 2  # 测试阶段每个源只抓2篇
TEST_MODE = True  # 测试模式：只抓前3个源

# ============= 1. 读取RSS源配置 =============
def load_rss_sources():
    """从 rss_sources_for_ai_students.json 读取RSS源"""
    with open(RSS_CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)

    sources = config['sources']

    # 过滤掉视频和播客（只保留文章、教学、实验室、论文）
    article_sources = [s for s in sources if s['category'] not in ['视频教程']]

    if TEST_MODE:
        # 测试模式：只取前3个最高优先级的源
        article_sources = [s for s in article_sources if s['priority'] == 'highest'][:3]
        print(f"【测试模式】只抓取 {len(article_sources)} 个源")

    return article_sources

# ============= 2. 抓取单个RSS源 =============
def fetch_rss_articles(source, max_articles=2):
    """抓取单个RSS源的文章"""
    print(f"\n正在抓取: {source['name']} ({source['url']})")

    try:
        feed = feedparser.parse(source['url'])

        if feed.bozo:  # RSS解析错误
            print(f"  ⚠️  RSS解析错误: {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries[:max_articles]:
            # 提取文章内容
            content = ""
            if hasattr(entry, 'content'):
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description

            article = {
                'title': entry.get('title', 'No Title'),
                'url': entry.get('link', ''),
                'published': entry.get('published', ''),
                'content': content,
                'source_name': source['name'],
                'source_category': source['category'],
                'source_priority': source['priority'],
                'source_difficulty': source['difficulty'],
            }
            articles.append(article)

        print(f"  ✓ 成功抓取 {len(articles)} 篇文章")
        return articles

    except Exception as e:
        print(f"  ✗ 抓取失败: {e}")
        return []

# ============= 3. 初始化数据库 =============
def init_database():
    """创建数据库表"""
    import os
    os.makedirs('data', exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # 创建文章表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        source_name TEXT,
        source_category TEXT,
        source_priority TEXT,
        source_difficulty TEXT,

        published_date TEXT,
        fetched_date TEXT,

        content TEXT,
        word_count INTEGER,

        -- 分析结果字段（后续Dify填充）
        filter_score INTEGER DEFAULT NULL,
        filter_passed BOOLEAN DEFAULT NULL,
        analysis_result TEXT DEFAULT NULL,
        final_score INTEGER DEFAULT NULL,

        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print("✓ 数据库初始化完成")

# ============= 4. 保存文章到数据库 =============
def save_articles_to_db(articles):
    """保存文章到数据库"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    saved_count = 0
    duplicate_count = 0

    for article in articles:
        try:
            cursor.execute('''
            INSERT INTO articles (title, url, source_name, source_category,
                                source_priority, source_difficulty,
                                published_date, fetched_date, content, word_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['title'],
                article['url'],
                article['source_name'],
                article['source_category'],
                article['source_priority'],
                article['source_difficulty'],
                article['published'],
                datetime.now().isoformat(),
                article['content'],
                len(article['content'].split())
            ))
            saved_count += 1
        except sqlite3.IntegrityError:
            duplicate_count += 1

    conn.commit()
    conn.close()

    print(f"\n保存结果: {saved_count} 篇新文章, {duplicate_count} 篇重复")
    return saved_count

# ============= 5. 主函数 =============
def main():
    print("=" * 60)
    print("RSS文章爬虫 - 测试版")
    print("=" * 60)

    # 步骤1: 初始化数据库
    print("\n【步骤1】初始化数据库...")
    init_database()

    # 步骤2: 加载RSS源
    print("\n【步骤2】加载RSS源配置...")
    sources = load_rss_sources()
    print(f"✓ 加载了 {len(sources)} 个RSS源")
    for i, s in enumerate(sources, 1):
        print(f"  {i}. {s['name']} - {s['category']} - {s['priority']}")

    # 步骤3: 抓取文章
    print("\n【步骤3】开始抓取文章...")
    all_articles = []
    for source in sources:
        articles = fetch_rss_articles(source, MAX_ARTICLES_PER_SOURCE)
        all_articles.extend(articles)
        time.sleep(1)  # 避免请求过快

    print(f"\n✓ 总共抓取 {len(all_articles)} 篇文章")

    # 步骤4: 保存到数据库
    print("\n【步骤4】保存文章到数据库...")
    saved = save_articles_to_db(all_articles)

    # 步骤5: 显示摘要
    print("\n" + "=" * 60)
    print("抓取完成！")
    print("=" * 60)
    print(f"总抓取: {len(all_articles)} 篇")
    print(f"新保存: {saved} 篇")
    print(f"数据库: {DATABASE_FILE}")
    print("\n下一步: 运行 Dify 工作流进行文章分析")
    print("=" * 60)

if __name__ == '__main__':
    main()
