from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base, SessionLocal
from api.articles import router as articles_router
from api.rss_sources import router as rss_router
from api.batches import router as batches_router
from rss_fetcher import RSSFetcher
from contextlib import asynccontextmanager
import os

# 创建数据库表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 Starting ArticleAggregator Backend...")

    # 启动时执行一次RSS抓取
    print("📥 启动时抓取RSS文章...")
    db = SessionLocal()
    try:
        fetcher = RSSFetcher(db)
        stats = fetcher.fetch_all_sources(max_articles_per_source=10)
        print(f"✅ 启动抓取完成: 抓取 {stats['sources_fetched']} 个源, {stats['new_articles']} 篇新文章")
    except Exception as e:
        print(f"⚠️ 启动抓取失败: {e}")
    finally:
        db.close()

    print("✅ Backend started successfully!")

    yield

    # 关闭时
    print("🛑 Shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title="ArticleAggregator API",
    description="文章聚合器后端 API - 本地版本",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置（允许 Dify 调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本地开发允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查接口
@app.get("/api/health")
def health_check():
    return {
        "service": "ArticleAggregator Backend",
        "status": "healthy",
        "version": "1.0.0"
    }

# 注册路由
app.include_router(articles_router, tags=["Articles"])
app.include_router(rss_router, tags=["RSS Sources"])
app.include_router(batches_router, tags=["Batches"])

# 挂载前端静态文件（必须在最后）
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    # 运行在 8765 端口
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
