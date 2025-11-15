# ArticleAggregator 项目结构说明

## 目录结构

```
ArticleAggregator/
├── backend/                    # 后端服务（核心部分）
│   ├── api/                    # API路由
│   │   ├── articles.py         # 文章管理API
│   │   ├── rss_sources.py      # RSS源管理API
│   │   └── batches.py          # 批次管理API
│   ├── main.py                 # FastAPI主应用
│   ├── init_rss.py             # RSS源初始化脚本
│   ├── database.py             # 数据库配置
│   ├── models.py               # 数据模型
│   ├── rss_manager.py          # RSS源管理器
│   ├── rss_fetcher.py          # RSS抓取器
│   ├── scheduler.py            # 调度器（已废弃）
│   └── check_db.py             # 数据库检查工具
│
├── frontend/                   # 前端页面
│   ├── index.html              # 主页（批次列表）
│   ├── batch.html              # 批次详情页
│   └── style.css               # 样式文件
│
├── config/                     # 配置文件
│   └── opml/                   # OPML订阅源文件
│       ├── ArticleAggregator_RSS_ALL.opml       # 所有RSS源
│       ├── ArticleAggregator_RSS_Articles.opml  # 文章源
│       ├── ArticleAggregator_RSS_Podcasts.opml  # 播客源
│       ├── ArticleAggregator_RSS_Twitters.opml  # Twitter源
│       └── ArticleAggregator_RSS_Videos.opml    # 视频源
│
├── docs/                       # 文档
│   ├── ArticleAggregator_OpenAPI_Doc.md         # OpenAPI文档
│   ├── ArticleAggregator_RSS_Doc.md             # RSS使用文档
│   ├── 前端测试说明.md                           # 前端测试说明
│   └── *.md                                     # 其他技术文档
│
├── flows/                      # Dify工作流配置
│   └── Dify/
│       └── dsl/                # 工作流DSL文件
│
├── tests/                      # 测试文件（预留）
│
├── archive/                    # 归档文件
├── images/                     # 图片资源
│
├── README.md                   # 项目说明
├── CLAUDE.md                   # Claude Code项目指引
├── PROJECT_STRUCTURE.md        # 本文档
└── .gitignore                  # Git忽略配置

```

## 核心模块说明

### backend/ - 后端服务

**作为独立服务或集成到其他项目时的核心部分**

#### 主要文件

- `main.py` - FastAPI应用入口
  - 端口：8765
  - 启动时自动抓取RSS文章（无定时任务）
  - 提供API和静态文件服务

- `init_rss.py` - RSS源初始化
  - 从OPML导入RSS源
  - 首次抓取文章
  - 提取全文内容

- `database.py` - 数据库配置
  - SQLite数据库：`articles.db`
  - SQLAlchemy ORM

- `models.py` - 数据模型
  - RSSSource：RSS源
  - Article：文章

- `rss_manager.py` - RSS源管理
  - OPML导入/导出
  - RSS源增删改查

- `rss_fetcher.py` - RSS抓取
  - 抓取RSS feed
  - 提取文章全文
  - 转换为Markdown

#### API路由

- `api/articles.py` - 文章API
  - GET /api/articles - 文章列表
  - GET /api/articles/{id} - 文章详情
  - GET /api/resource/markdown?id={id} - Markdown内容

- `api/rss_sources.py` - RSS源API
  - GET /api/rss/sources - RSS源列表
  - POST /api/rss/fetch - 手动抓取
  - POST /api/rss/extract-content - 提取全文

- `api/batches.py` - 批次API
  - GET /api/batches - 批次列表
  - GET /api/batches/{date}/articles - 批次文章

### frontend/ - 前端页面

**轻量级前端，可选择性使用**

- 纯HTML/CSS/JavaScript
- 无需构建工具
- 通过backend的静态文件服务访问

### config/ - 配置文件

**集成时需要保留此目录**

- `config/opml/` - RSS订阅源配置
- OPML格式，可用RSS阅读器导入

## 集成到其他项目

### 方式一：作为独立后端服务

```bash
# 1. 复制整个backend目录到目标项目
cp -r ArticleAggregator/backend /path/to/your/project/

# 2. 复制config目录
cp -r ArticleAggregator/config /path/to/your/project/

# 3. 安装依赖
cd /path/to/your/project/backend
pip install fastapi uvicorn sqlalchemy feedparser requests beautifulsoup4 lxml

# 4. 运行服务
python main.py
```

### 方式二：集成到现有FastAPI项目

```python
# 在你的main.py中
from backend.api.articles import router as articles_router
from backend.api.rss_sources import router as rss_router
from backend.api.batches import router as batches_router

app.include_router(articles_router, tags=["Articles"])
app.include_router(rss_router, tags=["RSS Sources"])
app.include_router(batches_router, tags=["Batches"])
```

### 方式三：仅使用抓取功能

```python
from backend.database import SessionLocal
from backend.rss_fetcher import RSSFetcher

db = SessionLocal()
fetcher = RSSFetcher(db)
stats = fetcher.fetch_all_sources(max_articles_per_source=10)
db.close()
```

## 数据库

**位置**：`backend/articles.db`（SQLite）

**表结构**：
- `rss_sources` - RSS源表
- `articles` - 文章表

**迁移到其他数据库**：
修改 `backend/database.py` 中的 `SQLALCHEMY_DATABASE_URL`

## 运行要求

### 依赖

```txt
fastapi
uvicorn
sqlalchemy
feedparser
requests
beautifulsoup4
lxml
```

### Python版本

Python 3.8+

### 启动方式

```bash
# 初始化（首次运行）
cd backend
python init_rss.py

# 启动服务
python main.py
```

### 访问地址

- API文档：http://localhost:8765/docs
- 前端页面：http://localhost:8765/
- 健康检查：http://localhost:8765/api/health

## 定时抓取说明

**当前版本：仅启动时抓取一次**

如需定时抓取：
1. 使用 `scheduler.py`（已包含但未启用）
2. 或在外部使用cron/systemd timer调用API：
   ```bash
   curl -X POST http://localhost:8765/api/rss/fetch
   ```

## 注意事项

1. **backend目录自包含**：可独立运行，无需其他目录
2. **config目录必需**：包含OPML配置文件
3. **frontend目录可选**：如不需要可删除
4. **数据库文件**：首次运行自动创建
5. **端口冲突**：默认8765，可在main.py中修改

## 文件清单（集成必需）

**最小集成清单**：
```
backend/
├── api/
│   ├── articles.py
│   ├── rss_sources.py
│   └── batches.py
├── main.py
├── database.py
├── models.py
├── rss_manager.py
└── rss_fetcher.py

config/
└── opml/
    └── ArticleAggregator_RSS_Articles.opml
```

**可选文件**：
- `init_rss.py` - 如有其他初始化方式可省略
- `scheduler.py` - 当前未使用
- `check_db.py` - 调试工具
- `frontend/` - 如有自己的前端
