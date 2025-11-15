# ArticleAggregator 集成指南

## 快速集成步骤

### 1. 复制核心文件

```bash
# 复制backend目录
cp -r backend /your/project/path/

# 复制config目录
cp -r config /your/project/path/
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy feedparser requests beautifulsoup4 lxml
```

### 3. 初始化数据库

```bash
cd backend
python init_rss.py
# 按提示操作：输入y抓取文章，输入y提取全文
```

### 4. 启动服务

```bash
python main.py
```

服务将运行在 `http://localhost:8765`

## 目录结构（集成后）

```
YourProject/
├── backend/              # ArticleAggregator后端
│   ├── api/
│   ├── main.py
│   ├── articles.db       # 自动生成
│   └── ...
├── config/               # RSS配置
│   └── opml/
└── [你的其他文件]
```

## API端点

启动后可访问以下API：

### 文章管理
- `GET /api/articles` - 获取文章列表
- `GET /api/articles/{id}` - 获取文章详情

### 批次管理
- `GET /api/batches` - 获取批次列表
- `GET /api/batches/{date}/articles` - 获取批次文章

### RSS抓取
- `POST /api/rss/fetch` - 手动触发抓取
- `POST /api/rss/extract-content` - 提取全文

### 其他
- `GET /api/health` - 健康检查
- `GET /docs` - API文档（Swagger UI）

## 自定义配置

### 修改端口

编辑 `backend/main.py`：

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=你的端口, reload=True)
```

### 修改数据库

编辑 `backend/database.py`：

```python
# SQLite（默认）
SQLALCHEMY_DATABASE_URL = "sqlite:///./articles.db"

# PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

# MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost/dbname"
```

### 修改RSS源

编辑 `config/opml/ArticleAggregator_RSS_Articles.opml`

或通过API管理：
```bash
# 添加RSS源
curl -X POST http://localhost:8765/api/rss/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"源名称","rss_url":"RSS地址"}'
```

## 启动时行为

当前配置：**启动时自动抓取一次RSS文章**

如需禁用，编辑 `backend/main.py`，注释以下代码：

```python
# 启动时执行一次RSS抓取
# print("📥 启动时抓取RSS文章...")
# db = SessionLocal()
# try:
#     fetcher = RSSFetcher(db)
#     stats = fetcher.fetch_all_sources(max_articles_per_source=10)
#     print(f"✅ 启动抓取完成: ...")
# except Exception as e:
#     print(f"⚠️ 启动抓取失败: {e}")
# finally:
#     db.close()
```

## 定时抓取（可选）

### 方式1：使用cron（Linux/Mac）

```bash
# 编辑crontab
crontab -e

# 每6小时抓取一次
0 */6 * * * curl -X POST http://localhost:8765/api/rss/fetch
```

### 方式2：使用systemd timer（Linux）

创建 `/etc/systemd/system/rss-fetch.timer`：

```ini
[Unit]
Description=RSS Fetch Timer

[Timer]
OnCalendar=*-*-* 0/6:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 方式3：Windows计划任务

使用Windows任务计划程序，设置PowerShell脚本：

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8765/api/rss/fetch"
```

## 前端集成（可选）

如需使用前端页面：

1. 确保 `frontend/` 目录与 `backend/` 同级
2. 访问 `http://localhost:8765/`

如不需要前端：
- 删除 `frontend/` 目录
- 从 `backend/main.py` 中删除静态文件挂载代码

## 故障排查

### 1. 数据库文件权限错误
```bash
chmod 666 backend/articles.db
```

### 2. 端口被占用
修改 `main.py` 中的端口号

### 3. OPML文件找不到
确保 `config/opml/` 目录存在且包含OPML文件

### 4. RSS抓取失败
检查网络连接，某些RSS源可能需要代理

## 文档链接

- [项目结构说明](./PROJECT_STRUCTURE.md)
- [前端测试说明](./docs/前端测试说明.md)
- [OpenAPI文档](./docs/ArticleAggregator_OpenAPI_Doc.md)
- [RSS使用文档](./docs/ArticleAggregator_RSS_Doc.md)
