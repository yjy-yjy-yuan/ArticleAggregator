"""
定时任务调度器
负责：定时抓取RSS、提取全文
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
from rss_fetcher import RSSFetcher
import logging

logger = logging.getLogger(__name__)


class ArticleScheduler:
    """文章抓取调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("📅 Scheduler started")

    def start_rss_fetching(self, interval_hours: int = 6):
        """
        启动定时RSS抓取

        Args:
            interval_hours: 抓取间隔（小时）
        """
        logger.info("✅ RSS fetching will run once on startup")
        self._fetch_rss_job()

    def start_content_extraction(self, interval_minutes: int = 30):
        """
        启动定时全文提取

        Args:
            interval_minutes: 提取间隔（分钟）
        """
        self.scheduler.add_job(
            func=self._extract_content_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='extract_content',
            name='Extract article content',
            replace_existing=True
        )
        logger.info(f"✅ Content extraction scheduled: every {interval_minutes} minutes")

    def _fetch_rss_job(self):
        """RSS抓取任务"""
        logger.info("🚀 Starting RSS fetch job...")
        db = SessionLocal()
        try:
            fetcher = RSSFetcher(db)
            stats = fetcher.fetch_all_sources(max_articles_per_source=5)
            logger.info(f"✅ RSS fetch completed: {stats}")
        except Exception as e:
            logger.error(f"❌ RSS fetch error: {str(e)}")
        finally:
            db.close()

    def _extract_content_job(self):
        """全文提取任务"""
        logger.info("🚀 Starting content extraction job...")
        db = SessionLocal()
        try:
            fetcher = RSSFetcher(db)
            stats = fetcher.extract_batch_content(limit=10)
            logger.info(f"✅ Content extraction completed: {stats}")
        except Exception as e:
            logger.error(f"❌ Content extraction error: {str(e)}")
        finally:
            db.close()

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("📅 Scheduler stopped")

    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()
