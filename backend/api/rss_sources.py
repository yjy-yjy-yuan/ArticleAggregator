"""
RSS 源管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import get_db
from models import RSSSource
from rss_manager import RSSSourceManager
from rss_fetcher import RSSFetcher

router = APIRouter()


# Pydantic 模型
class RSSSourceCreate(BaseModel):
    name: str
    rss_url: str
    category: str = None
    language: str = "zh_CN"


class RSSSourceResponse(BaseModel):
    id: int
    name: str
    title: str
    rss_url: str
    category: str
    language: str
    enabled: bool
    last_fetched_at: str = None

    class Config:
        from_attributes = True


class OPMLImportRequest(BaseModel):
    opml_file_path: str


# ========== RSS 源管理接口 ==========

@router.post("/api/rss/sources", response_model=RSSSourceResponse)
def create_rss_source(
    source_data: RSSSourceCreate,
    db: Session = Depends(get_db)
):
    """添加新的 RSS 源"""
    manager = RSSSourceManager(db)
    try:
        source = manager.add_source(
            name=source_data.name,
            rss_url=source_data.rss_url,
            category=source_data.category,
            language=source_data.language
        )
        return source
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/rss/sources", response_model=List[RSSSourceResponse])
def list_rss_sources(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取 RSS 源列表"""
    manager = RSSSourceManager(db)
    sources = manager.list_sources(enabled_only=enabled_only)
    return sources


@router.post("/api/rss/import-opml")
def import_opml(
    request: OPMLImportRequest,
    db: Session = Depends(get_db)
):
    """从 OPML 文件导入 RSS 源"""
    manager = RSSSourceManager(db)
    try:
        stats = manager.import_from_opml(request.opml_file_path)
        return {
            "message": "OPML import completed",
            "stats": stats
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/rss/sources/{source_id}/enable")
def enable_source(source_id: int, db: Session = Depends(get_db)):
    """启用 RSS 源"""
    manager = RSSSourceManager(db)
    manager.enable_source(source_id)
    return {"message": f"Source {source_id} enabled"}


@router.post("/api/rss/sources/{source_id}/disable")
def disable_source(source_id: int, db: Session = Depends(get_db)):
    """禁用 RSS 源"""
    manager = RSSSourceManager(db)
    manager.disable_source(source_id)
    return {"message": f"Source {source_id} disabled"}


@router.delete("/api/rss/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """删除 RSS 源"""
    manager = RSSSourceManager(db)
    manager.delete_source(source_id)
    return {"message": f"Source {source_id} deleted"}


# ========== 抓取控制接口 ==========

@router.post("/api/rss/fetch")
def fetch_rss_feeds(
    background_tasks: BackgroundTasks,
    max_articles_per_source: int = 5,
    db: Session = Depends(get_db)
):
    """手动触发 RSS 抓取"""

    def fetch_task():
        fetcher = RSSFetcher(db)
        stats = fetcher.fetch_all_sources(max_articles_per_source)
        print(f"✅ Fetch completed: {stats}")

    background_tasks.add_task(fetch_task)
    return {"message": "RSS fetch started in background"}


@router.post("/api/rss/extract-content")
def extract_content(
    background_tasks: BackgroundTasks,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """手动触发全文提取"""

    def extract_task():
        fetcher = RSSFetcher(db)
        stats = fetcher.extract_batch_content(limit)
        print(f"✅ Extraction completed: {stats}")

    background_tasks.add_task(extract_task)
    return {"message": "Content extraction started in background"}
