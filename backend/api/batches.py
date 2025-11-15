"""
文章批次管理 API - 用于前端展示
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime
from pydantic import BaseModel
from database import get_db
from models import Article

router = APIRouter()


class BatchInfo(BaseModel):
    """批次信息"""
    batch_id: int  # 批次号（从1开始）
    batch_date: str  # 批次日期
    article_count: int  # 文章数量
    first_article_time: str  # 第一篇文章时间


class ArticleBrief(BaseModel):
    """文章简要信息"""
    id: str
    title: str
    summary: str
    author: str = None
    url: str
    published_at: str = None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/api/batches", response_model=List[BatchInfo])
def list_batches(db: Session = Depends(get_db)):
    """
    获取所有文章批次列表
    按创建日期分组，每天的文章作为一个批次
    """
    # 按日期分组统计
    results = db.query(
        func.date(Article.created_at).label('batch_date'),
        func.count(Article.id).label('article_count'),
        func.min(Article.created_at).label('first_article_time')
    ).group_by(
        func.date(Article.created_at)
    ).order_by(
        desc(func.date(Article.created_at))
    ).all()

    batches = []
    for idx, (batch_date, article_count, first_time) in enumerate(results, 1):
        batches.append(BatchInfo(
            batch_id=idx,
            batch_date=str(batch_date),
            article_count=article_count,
            first_article_time=first_time.isoformat() if first_time else ""
        ))

    return batches


@router.get("/api/batches/{batch_date}/articles", response_model=List[ArticleBrief])
def get_batch_articles(
    batch_date: str,  # 格式：YYYY-MM-DD
    db: Session = Depends(get_db)
):
    """
    获取指定批次的文章列表
    """
    # 查询指定日期创建的文章
    articles = db.query(Article).filter(
        func.date(Article.created_at) == batch_date
    ).order_by(
        desc(Article.created_at)
    ).all()

    if not articles:
        raise HTTPException(status_code=404, detail=f"No articles found for batch {batch_date}")

    return [
        ArticleBrief(
            id=article.id,
            title=article.title,
            summary=article.summary or "暂无摘要",
            author=article.author,
            url=article.url,
            published_at=article.published_at.isoformat() if article.published_at else None,
            created_at=article.created_at.isoformat()
        )
        for article in articles
    ]
