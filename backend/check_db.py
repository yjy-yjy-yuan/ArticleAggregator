"""
检查数据库状态

快速诊断工具，查看数据库中的数据
"""

import sys
from database import SessionLocal
from models import RSSSource, Article
from sqlalchemy import func

def check_database():
    """检查数据库状态"""
    print("=" * 60)
    print("📊 ArticleAggregator - 数据库状态检查")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. RSS 源统计
        total_sources = db.query(func.count(RSSSource.id)).scalar()
        enabled_sources = db.query(func.count(RSSSource.id)).filter(
            RSSSource.enabled == True
        ).scalar()

        print(f"\n📚 RSS 源:")
        print(f"   总数: {total_sources}")
        print(f"   启用: {enabled_sources}")
        print(f"   禁用: {total_sources - enabled_sources}")

        # 2. 文章统计
        total_articles = db.query(func.count(Article.id)).scalar()
        pending_articles = db.query(func.count(Article.id)).filter(
            Article.fetch_status == "pending"
        ).scalar()
        fetched_articles = db.query(func.count(Article.id)).filter(
            Article.fetch_status == "fetched"
        ).scalar()
        failed_articles = db.query(func.count(Article.id)).filter(
            Article.fetch_status == "failed"
        ).scalar()

        print(f"\n📄 文章:")
        print(f"   总数: {total_articles}")
        print(f"   待提取全文: {pending_articles}")
        print(f"   已提取: {fetched_articles}")
        print(f"   提取失败: {failed_articles}")

        # 3. 最新文章
        if total_articles > 0:
            print(f"\n📰 最新 5 篇文章:")
            recent_articles = db.query(Article).order_by(
                Article.created_at.desc()
            ).limit(5).all()

            for i, article in enumerate(recent_articles, 1):
                print(f"\n   {i}. {article.title[:60]}...")
                print(f"      ID: {article.id}")
                print(f"      URL: {article.url[:80]}")
                print(f"      状态: {article.fetch_status}")
                print(f"      分类: {article.category}")

        # 4. 按源统计文章数
        print(f"\n📊 各源文章数（Top 10）:")
        source_stats = db.query(
            RSSSource.name,
            func.count(Article.id).label('article_count')
        ).join(Article).group_by(RSSSource.id).order_by(
            func.count(Article.id).desc()
        ).limit(10).all()

        for source_name, count in source_stats:
            print(f"   {source_name}: {count} 篇")

        print("\n" + "=" * 60)

        # 5. 建议
        if total_articles == 0:
            print("\n⚠️  数据库中没有文章！")
            print("\n可能原因:")
            print("1. RSS 源没有文章（feed 为空）")
            print("2. 所有文章都被认为是重复的")
            print("3. RSS 源地址无效")
            print("\n建议:")
            print("1. 运行: python init_rss.py 重新抓取")
            print("2. 或删除数据库: rm -rf data/articles.db")
            print("3. 然后重新初始化")
        elif pending_articles > 0:
            print(f"\n💡 提示: 有 {pending_articles} 篇文章待提取全文")
            print("运行以下命令手动触发提取:")
            print("curl -X POST http://localhost:8765/api/rss/extract-content")

        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    check_database()
