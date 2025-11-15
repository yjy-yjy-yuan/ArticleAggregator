# ArticleAggregator Backend

RSS 文章聚合系统，自动抓取文章并提供 API 接口。

## 快速启动

```bash
# 1. 安装依赖
conda create -n article python=3.10 -y
conda activate article
pip install -r requirements.txt

# 2. 初始化 RSS 源（首次运行）
python init_rss.py
# 选择 y 抓取文章，选择 y 提取全文

# 3. 启动服务
python main.py
```

**服务地址**: http://localhost:8765
**API 文档**: http://localhost:8765/docs

## 验证

```bash
# 检查服务
curl http://localhost:8765/health

# 查看数据库状态
python check_db.py

# 测试获取文章
curl "http://localhost:8765/api/articles?limit=1"
```

## 核心接口

### Dify 工作流使用
```
GET /api/resource/markdown?id={article_id}
```

### 管理接口
```
GET  /api/articles              # 文章列表
GET  /api/rss/sources           # RSS 源列表
POST /api/rss/fetch             # 手动抓取
POST /api/rss/extract-content   # 手动提取全文
```

## 自动任务

- **每 6 小时**: 自动抓取 RSS
- **每 30 分钟**: 自动提取全文

修改频率: 编辑 `main.py` 中的 `scheduler.start_*` 参数

## 添加 RSS 源

编辑 `../ArticleAggregator_RSS_Articles.opml`:
```xml
<outline text="博客名" title="博客名" type="rss" xmlUrl="RSS地址"/>
```

然后运行 `python init_rss.py`

## 常用命令

```bash
# 检查状态
python check_db.py

# 清空数据库重新开始
rm -rf data/articles.db
python init_rss.py

# 手动触发抓取
curl -X POST http://localhost:8765/api/rss/fetch

# 手动提取全文
curl -X POST http://localhost:8765/api/rss/extract-content?limit=50
```

## Dify 集成

修改工作流 DSL 中的 API 地址:
```yaml
# 将 https://api.bestblogs.dev 替换为
url: http://host.docker.internal:8765
```

**注意**: 使用 `host.docker.internal` 因为 Dify 在 Docker 容器中。
