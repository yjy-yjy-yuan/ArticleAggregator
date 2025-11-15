"""
初始化 RSS 源

从 OPML 文件导入 RSS 源并触发首次抓取
"""

import sys
import os
from database import SessionLocal, engine, Base
from rss_manager import RSSSourceManager
from rss_fetcher import RSSFetcher

# 创建数据库表（如果不存在）
print("🔧 检查并创建数据库表...")
Base.metadata.create_all(bind=engine)
print("✅ 数据库表已就绪\n")

# OPML 文件路径（ArticleAggregator_RSS_Articles.opml）
OPML_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "ArticleAggregator_RSS_Articles.opml"
)


def init_rss_sources():
    """导入 RSS 源"""
    print("=" * 60)
    print("📚 ArticleAggregator - RSS 源初始化")
    print("=" * 60)

    if not os.path.exists(OPML_FILE):
        print(f"\n❌ OPML 文件不存在: {OPML_FILE}")
        print(f"\n请确认路径是否正确")
        return False

    db = SessionLocal()

    try:
        # 1. 导入 OPML
        print(f"\n📥 正在导入 OPML 文件...")
        print(f"   文件路径: {OPML_FILE}")

        manager = RSSSourceManager(db)
        stats = manager.import_from_opml(OPML_FILE)

        print(f"\n✅ OPML 导入完成:")
        print(f"   总数: {stats['total']}")
        print(f"   新增: {stats['new']}")
        print(f"   已存在: {stats['existing']}")

        if stats['new'] == 0:
            print(f"\n⚠️  没有新的 RSS 源，可能已经导入过了")
            return True

        # 2. 询问是否立即抓取
        print(f"\n" + "=" * 60)
        choice = input("是否立即抓取文章？(y/n): ").strip().lower()

        if choice == 'y':
            print(f"\n🚀 开始抓取 RSS feed...")
            print(f"   每个源最多抓取 10 篇文章")

            fetcher = RSSFetcher(db)
            fetch_stats = fetcher.fetch_all_sources(max_articles_per_source=10)

            print(f"\n✅ RSS 抓取完成:")
            print(f"   抓取源数: {fetch_stats['sources_fetched']}")
            print(f"   新文章数: {fetch_stats['new_articles']}")
            print(f"   错误数: {fetch_stats['errors']}")

            if fetch_stats['new_articles'] > 0:
                # 3. 提取全文
                print(f"\n" + "=" * 60)
                extract_choice = input("是否提取文章全文（转换为 Markdown）？(y/n): ").strip().lower()

                if extract_choice == 'y':
                    print(f"\n📝 开始提取全文...")
                    print(f"   （这可能需要一些时间，取决于文章数量）")

                    extract_stats = fetcher.extract_batch_content(limit=20)

                    print(f"\n✅ 全文提取完成:")
                    print(f"   处理总数: {extract_stats['total']}")
                    print(f"   成功: {extract_stats['success']}")
                    print(f"   失败: {extract_stats['failed']}")

        print(f"\n" + "=" * 60)
        print("🎉 初始化完成！")
        print(f"\n后续抓取将自动进行:")
        print(f"   - RSS 抓取: 每 6 小时")
        print(f"   - 全文提取: 每 30 分钟")
        print(f"\n你也可以通过 API 手动触发:")
        print(f"   POST http://localhost:8765/api/rss/fetch")
        print(f"   POST http://localhost:8765/api/rss/extract-content")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = init_rss_sources()
    sys.exit(0 if success else 1)
