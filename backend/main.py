from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api.articles import router as articles_router
from api.rss_sources import router as rss_router
from scheduler import ArticleScheduler
from contextlib import asynccontextmanager

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 全局调度器
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global scheduler

    # 启动时
    print("🚀 Starting ArticleAggregator Backend...")

    # 启动调度器
    scheduler = ArticleScheduler()
    scheduler.start_rss_fetching(interval_hours=6)  # 每6小时抓取RSS
    scheduler.start_content_extraction(interval_minutes=30)  # 每30分钟提取全文

    print("✅ Backend started successfully!")

    yield

    # 关闭时
    print("🛑 Shutting down...")
    if scheduler:
        scheduler.stop()


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

# 注册路由
app.include_router(articles_router, tags=["Articles"])
app.include_router(rss_router, tags=["RSS Sources"])

# 健康检查接口
@app.get("/")
def root():
    return {
        "service": "ArticleAggregator Backend",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # 运行在 8765 端口
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
