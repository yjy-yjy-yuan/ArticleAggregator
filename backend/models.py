from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from pydantic import BaseModel
from typing import Optional

# SQLAlchemy ORM 模型 - RSS 源
class RSSSource(Base):
    __tablename__ = "rss_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # RSS 源名称
    title = Column(String)  # RSS 源标题
    rss_url = Column(String, unique=True, nullable=False)  # RSS 订阅地址
    website_url = Column(String)  # 网站地址
    category = Column(String)  # 分类
    language = Column(String, default="zh_CN")  # 语言
    enabled = Column(Boolean, default=True)  # 是否启用
    last_fetched_at = Column(DateTime)  # 最后抓取时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    articles = relationship("Article", back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, index=True)  # 文章ID，基于URL的hash
    source_id = Column(Integer, ForeignKey("rss_sources.id"))  # 所属RSS源
    title = Column(String, nullable=False)
    author = Column(String)
    url = Column(String, unique=True, nullable=False, index=True)  # 原文链接（用于去重）
    summary = Column(Text)  # 摘要
    markdown_content = Column(Text)  # Markdown 格式文章内容（可能为空，需要全文提取）
    published_at = Column(DateTime)  # 发布时间
    category = Column(String)  # 分类
    language = Column(String, default="zh_CN")
    fetch_status = Column(String, default="pending")  # pending, fetched, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    source = relationship("RSSSource", back_populates="articles")

# Pydantic 模型（用于 API 请求/响应）
class ArticleCreate(BaseModel):
    id: str
    title: str
    author: Optional[str] = None
    url: Optional[str] = None
    markdown_content: str
    category: Optional[str] = "Programming_Technology"
    language: Optional[str] = "zh_CN"

class ArticleResponse(BaseModel):
    id: str
    title: str
    author: Optional[str]
    url: Optional[str]
    category: Optional[str]
    language: str
    created_at: datetime

    class Config:
        from_attributes = True

class MarkdownResponse(BaseModel):
    """Dify 工作流需要的响应格式"""
    content: str  # Markdown 内容
