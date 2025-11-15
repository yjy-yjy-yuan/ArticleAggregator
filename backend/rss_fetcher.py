"""
RSS 抓取模块
负责：抓取 RSS feed、提取文章元数据、提取全文并转换为 Markdown
"""

import feedparser
import trafilatura
import hashlib
import requests
from sqlalchemy.orm import Session
from models import RSSSource, Article
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSFetcher:
    """RSS 抓取器"""

    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArticleAggregator/1.0 (RSS Reader)'
        })

    def fetch_all_sources(self, max_articles_per_source: int = 10) -> Dict[str, int]:
        """
        抓取所有启用的 RSS 源

        Args:
            max_articles_per_source: 每个源最多抓取文章数

        Returns:
            统计信息 {"sources_fetched": 源数量, "new_articles": 新文章数, "errors": 错误数}
        """
        sources = self.db.query(RSSSource).filter(RSSSource.enabled == True).all()

        stats = {
            "sources_fetched": 0,
            "new_articles": 0,
            "errors": 0
        }

        for source in sources:
            try:
                new_count = self.fetch_source(source, max_articles_per_source)
                stats["new_articles"] += new_count
                stats["sources_fetched"] += 1

                # 更新最后抓取时间
                source.last_fetched_at = datetime.utcnow()
                self.db.commit()

                logger.info(f"✅ Fetched {source.name}: {new_count} new articles")

                # 避免请求过快
                time.sleep(1)

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"❌ Error fetching {source.name}: {str(e)}")

        return stats

    def fetch_source(self, source: RSSSource, max_articles: int = 10) -> int:
        """
        抓取单个 RSS 源

        Args:
            source: RSS 源对象
            max_articles: 最多抓取文章数

        Returns:
            新增文章数量
        """
        # 解析 RSS feed
        feed = feedparser.parse(source.rss_url)

        if feed.bozo:  # 解析错误
            logger.warning(f"Feed parse error for {source.name}: {feed.bozo_exception}")

        # 检查是否有文章
        if not feed.entries:
            logger.debug(f"No entries found for {source.name}")
            return 0

        new_count = 0
        duplicate_count = 0
        entries = feed.entries[:max_articles]  # 限制数量

        logger.debug(f"Processing {len(entries)} entries from {source.name}")

        for entry in entries:
            try:
                # 获取文章链接
                url = entry.get("link", "")
                if not url:
                    continue

                # 检查是否已存在（根据URL去重）
                exists = self.db.query(Article).filter(Article.url == url).first()
                if exists:
                    duplicate_count += 1
                    continue

                # 提取元数据
                title = entry.get("title", "Untitled")
                author = entry.get("author", source.name)
                summary = entry.get("summary", "")

                # 解析发布时间
                published_at = self._parse_date(entry.get("published", ""))

                # 生成文章ID（基于URL的hash）
                article_id = self._generate_article_id(url)

                # 创建文章记录（暂不提取全文）
                article = Article(
                    id=article_id,
                    source_id=source.id,
                    title=title,
                    author=author,
                    url=url,
                    summary=self._clean_html(summary),
                    published_at=published_at,
                    category=source.category,
                    language=source.language,
                    fetch_status="pending"  # 待提取全文
                )

                self.db.add(article)
                new_count += 1

            except Exception as e:
                logger.error(f"Error processing entry from {source.name}: {str(e)}")

        self.db.commit()

        # 输出统计信息
        if duplicate_count > 0:
            logger.debug(f"{source.name}: {new_count} new, {duplicate_count} duplicates")

        return new_count

    def extract_full_content(self, article: Article) -> bool:
        """
        提取文章全文并转换为 Markdown

        Args:
            article: 文章对象

        Returns:
            是否成功
        """
        try:
            # 使用 trafilatura 提取全文
            downloaded = trafilatura.fetch_url(article.url)

            if not downloaded:
                article.fetch_status = "failed"
                article.markdown_content = article.summary  # 降级使用摘要
                self.db.commit()
                return False

            # 提取并转换为 Markdown
            markdown_content = trafilatura.extract(
                downloaded,
                output_format='markdown',
                include_links=True,
                include_images=True,
                include_tables=True
            )

            if not markdown_content:
                article.fetch_status = "failed"
                article.markdown_content = article.summary
                self.db.commit()
                return False

            # 更新文章
            article.markdown_content = markdown_content
            article.fetch_status = "fetched"
            self.db.commit()

            logger.info(f"✅ Extracted full content: {article.title[:50]}...")
            return True

        except Exception as e:
            logger.error(f"❌ Error extracting {article.url}: {str(e)}")
            article.fetch_status = "failed"
            article.markdown_content = article.summary
            self.db.commit()
            return False

    def extract_batch_content(self, limit: int = 10) -> Dict[str, int]:
        """
        批量提取待处理文章的全文

        Args:
            limit: 一次处理的文章数量

        Returns:
            统计信息
        """
        # 获取待提取的文章
        pending_articles = self.db.query(Article).filter(
            Article.fetch_status == "pending"
        ).limit(limit).all()

        stats = {
            "total": len(pending_articles),
            "success": 0,
            "failed": 0
        }

        for article in pending_articles:
            if self.extract_full_content(article):
                stats["success"] += 1
            else:
                stats["failed"] += 1

            # 避免请求过快
            time.sleep(2)

        return stats

    def _generate_article_id(self, url: str) -> str:
        """生成文章ID（基于URL的短hash）"""
        hash_obj = hashlib.md5(url.encode())
        short_hash = hash_obj.hexdigest()[:12]
        return f"ART_{short_hash}"

    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return datetime.utcnow()

        try:
            return date_parser.parse(date_str)
        except:
            return datetime.utcnow()

    def _clean_html(self, html_text: str) -> str:
        """清理HTML标签"""
        if not html_text:
            return ""

        # 使用 trafilatura 清理
        return trafilatura.extract(html_text, output_format='txt') or html_text[:500]
