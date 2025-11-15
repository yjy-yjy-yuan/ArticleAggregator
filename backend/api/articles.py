from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from models import Article, ArticleCreate, ArticleResponse, MarkdownResponse
from database import get_db

router = APIRouter()

# ========== Dify 工作流核心接口 ==========

@router.get("/api/resource/markdown", response_model=MarkdownResponse)
def get_article_markdown(
    id: str = Query(..., description="文章ID"),
    db: Session = Depends(get_db)
):
    """
    获取文章 Markdown 内容（Dify 工作流调用）

    兼容原 BestBlogs API 格式：
    GET /api/resource/markdown?id=ART_001
    """
    article = db.query(Article).filter(Article.id == id).first()

    if not article:
        raise HTTPException(status_code=404, detail=f"Article {id} not found")

    return MarkdownResponse(content=article.markdown_content)


# ========== 文章管理接口（可选） ==========

@router.post("/api/articles", response_model=ArticleResponse, status_code=201)
def create_article(
    article_data: ArticleCreate,
    db: Session = Depends(get_db)
):
    """创建新文章"""
    # 检查文章ID是否已存在
    existing = db.query(Article).filter(Article.id == article_data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Article {article_data.id} already exists")

    article = Article(**article_data.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.get("/api/articles", response_model=List[ArticleResponse])
def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    query = db.query(Article)

    if category:
        query = query.filter(Article.category == category)

    articles = query.offset(skip).limit(limit).all()
    return articles


@router.get("/api/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: str, db: Session = Depends(get_db)):
    """获取单篇文章详情"""
    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

    return article


@router.delete("/api/articles/{article_id}")
def delete_article(article_id: str, db: Session = Depends(get_db)):
    """删除文章"""
    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

    db.delete(article)
    db.commit()

    return {"message": f"Article {article_id} deleted successfully"}
