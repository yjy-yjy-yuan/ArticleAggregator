# AI学生知识库集成指南

> 将 `rss_sources_for_ai_students.json` 集成到自己的文章聚合工作流中

## 📋 项目目标

构建一个**专为AI/ML学生定制**的智能文章聚合系统，完全独立于 BestBlogs.dev，使用自己的RSS源和工作流。

### 核心特点
- ✅ 只关注**文章类内容**（移除播客、视频、推文）
- ✅ 使用 `rss_sources_for_ai_students.json` 中的 25 个精选源
- ✅ 基于 Dify Workflow 的智能分析流程
- ✅ 适配AI学生的评分和分类体系

---

## 🗂️ 项目文件结构

```
G:\ArticleAggregator/
├── test_ai_student_config.json          # ⭐ 测试配置文件（新建）
├── AI_STUDENT_INTEGRATION_GUIDE.md      # ⭐ 本集成指南（新建）
├── rss_sources_for_ai_students.json     # 📌 你的RSS源定义
│
├── data/                                # 数据存储目录
│   └── ai_student_articles.db           # SQLite 数据库
│
├── flows/Dify/dsl/                      # Dify 工作流定义
│   ├── ai_student_filter.yml            # ⭐ 待创建：AI学生初评流程
│   ├── ai_student_analysis.yml          # ⭐ 待创建：AI学生分析流程
│   └── ai_student_translate.yml         # ⭐ 可选：翻译流程
│
└── logs/                                # 日志目录（建议创建）
```

---

## 🚀 快速开始（测试流程）

### 第一步：验证测试配置

已为你创建 `test_ai_student_config.json`，包含：
- **7 个高质量RSS源**（从 25 个中精选）
- **完整的工作流参数**
- **AI学生专属的分类体系**

```bash
# 查看配置文件
cat test_ai_student_config.json
```

#### 测试阶段启用的 7 个源：

| ID | 源名称 | 类别 | 难度 | 优先级 | 更新频率 |
|----|--------|------|------|--------|---------|
| 1 | Jay Alammar | 教学与可视化 | 本科生 | highest | 低频高质 |
| 2 | OpenAI Blog | 顶级实验室 | 研究生 | highest | 中频 |
| 3 | Hugging Face Blog | 实践应用 | 本科生 | highest | 高频 |
| 4 | Lilian Weng | 教学与可视化 | 研究生 | highest | 低频高质 |
| 5 | DeepMind Blog | 顶级实验室 | 研究生 | high | 中频 |
| 6 | PyTorch Blog | 实践应用 | 本科生 | high | 中频 |
| 7 | Distill | 教学与可视化 | 研究生 | high | 极低频极高质 |

**arXiv cs.LG** 暂时禁用（避免测试阶段文章过多）

---

### 第二步：RSS 抓取实现

你需要实现一个简单的 RSS 爬虫（当前项目中没有爬虫代码）。

#### 选项 A：Python 实现（推荐）

```python
# rss_crawler.py
import feedparser
import json
import sqlite3
from datetime import datetime

def load_test_sources():
    """加载测试配置中的RSS源"""
    with open('test_ai_student_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return [s for s in config['test_sources'] if s['enabled']]

def fetch_rss_feed(url, max_articles=3):
    """抓取单个RSS源"""
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:max_articles]:
        article = {
            'title': entry.get('title', ''),
            'url': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', ''),
            'content': entry.get('content', [{}])[0].get('value', ''),
        }
        articles.append(article)

    return articles

def main():
    sources = load_test_sources()

    for source in sources:
        print(f"抓取: {source['name']}...")
        articles = fetch_rss_feed(source['url'], max_articles=3)
        print(f"  获取 {len(articles)} 篇文章")

        # TODO: 保存到数据库或调用 Dify API

if __name__ == '__main__':
    main()
```

#### 选项 B：使用 RSSHub 或现有服务

如果你已经有 RSS 服务（如 BestBlogs 的后端），可以：
1. 导入 `test_ai_student_config.json` 中的源
2. 配置抓取参数（每源3篇，总计20篇/天）

---

### 第三步：配置 Dify 工作流

基于现有的 `Atricle分析流程-V2.yml`，针对 AI 学生场景进行调整。

#### 3.1 初评流程调整

**文件**: `flows/Dify/dsl/ai_student_filter.yml`

**关键修改**:
```yaml
# 初评提示词调整
system_prompt: |
  你是一个专为AI/ML学生设计的内容过滤器。

  评估标准：
  1. 学术价值（40分）：是否有助于学生理解ML/DL概念
  2. 实践价值（30分）：是否提供代码、实验或案例
  3. 相关性（30分）：是否聚焦AI核心领域

  自动过滤：
  - 商业/市场营销文章
  - 产品设计/UX内容
  - 纯工程实践（DevOps、云计算等非AI内容）
  - 新闻快讯（除非来自顶级实验室）

  通过阈值：60分
```

#### 3.2 分析流程调整

**文件**: `flows/Dify/dsl/ai_student_analysis.yml`

**关键修改**:

1. **领域分类**改为AI学生专属：
```json
{
  "domains": [
    "机器学习基础",
    "深度学习",
    "自然语言处理",
    "计算机视觉",
    "强化学习",
    "AI工具与框架"
  ]
}
```

2. **评分权重**调整：
```yaml
scoring_weights:
  academic_depth: 0.35    # 学术深度（提高）
  relevance: 0.30         # 相关性
  practicality: 0.20      # 实用性
  innovation: 0.15        # 创新性
```

3. **标签体系**针对学生需求：
```yaml
tag_categories:
  - 技术主题: [Transformer, CNN, RNN, LSTM, Attention, ...]
  - 学习难度: [入门, 进阶, 高级, 论文级]
  - 内容类型: [教程, 论文解读, 实践案例, 工具介绍]
  - 代码语言: [PyTorch, TensorFlow, JAX, ...]
```

---

### 第四步：创建数据库

```bash
# 创建数据目录
mkdir -p data

# 使用 SQLite
sqlite3 data/ai_student_articles.db
```

**表结构**（建议）:
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source_name TEXT,
    published_date DATETIME,
    fetched_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 文章内容
    content_markdown TEXT,
    word_count INTEGER,
    language TEXT,

    -- 初评结果
    filter_score INTEGER,
    filter_passed BOOLEAN,

    -- 分析结果
    one_sentence_summary TEXT,
    summary TEXT,
    domain TEXT,
    tags TEXT,  -- JSON array
    main_points TEXT,  -- JSON array
    key_quotes TEXT,  -- JSON array
    final_score INTEGER,

    -- 翻译结果（可选）
    summary_zh TEXT,

    -- 状态
    status TEXT DEFAULT 'pending',  -- pending, filtered, analyzed, featured
    featured BOOLEAN DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source ON articles(source_name);
CREATE INDEX idx_score ON articles(final_score);
CREATE INDEX idx_status ON articles(status);
CREATE INDEX idx_domain ON articles(domain);
```

---

### 第五步：集成 Dify API

调用 Dify 工作流的示例代码：

```python
import requests
import json

DIFY_API_KEY = "your-dify-api-key"
DIFY_WORKFLOW_URL = "https://api.dify.ai/v1/workflows/run"

def analyze_article_with_dify(article_data):
    """调用 Dify 分析工作流"""

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "article_title": article_data['title'],
            "article_url": article_data['url'],
            "article_content": article_data['content'],
            "source_name": article_data['source_name'],
            "word_count": len(article_data['content'].split())
        },
        "response_mode": "blocking",
        "user": "ai_student_system"
    }

    response = requests.post(DIFY_WORKFLOW_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['data']['outputs']
    else:
        print(f"错误: {response.status_code}")
        return None

# 使用示例
article = {
    'title': 'Understanding Transformers',
    'url': 'https://...',
    'content': '...',
    'source_name': 'Jay Alammar'
}

analysis_result = analyze_article_with_dify(article)
print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
```

---

## 📊 测试验证清单

### 第一周测试目标

- [ ] **RSS 抓取**
  - [ ] 成功抓取 7 个源的文章
  - [ ] 每个源限制 3 篇
  - [ ] 总计获取 15-20 篇文章

- [ ] **初评流程**
  - [ ] 至少 50% 文章通过初评（阈值 60 分）
  - [ ] 正确过滤掉营销/非AI内容
  - [ ] 记录每篇文章的初评分数

- [ ] **分析流程**
  - [ ] 成功生成一句话总结
  - [ ] 正确识别领域分类（6个类别）
  - [ ] 评分在 50-95 分范围内
  - [ ] 标签数量 3-8 个

- [ ] **数据存储**
  - [ ] 文章保存到 SQLite
  - [ ] 可以查询高分文章（score >= 85）
  - [ ] 可以按领域筛选

---

## 🔧 常见问题

### Q1: 如何调整评分阈值？

编辑 `test_ai_student_config.json`:
```json
"quality_control": {
  "initial_filter_threshold": 60,      // 初评通过线
  "deep_analysis_threshold": 70,       // 深度分析线
  "featured_threshold": 85,            // 精选文章线
  "auto_reject_below": 50              // 自动拒绝线
}
```

### Q2: Dify 工作流如何导入？

1. 复制 `Atricle分析流程-V2.yml` 内容
2. 登录 Dify 平台
3. 创建新工作流 → 导入 DSL
4. 根据上述指南修改提示词和参数
5. 测试运行并获取 API 密钥

### Q3: 如何启用 arXiv 论文源？

测试稳定后，在 `test_ai_student_config.json` 中：
```json
{
  "id": 8,
  "name": "arXiv cs.LG",
  "enabled": true,  // 改为 true
  ...
}
```

同时调整：
```json
"workflow_config": {
  "crawling": {
    "max_articles_per_source": 5,    // arXiv 增加到 5 篇
    "total_daily_limit": 50          // 总量上限提高
  }
}
```

### Q4: 翻译流程必须启用吗？

不必须。建议：
- 如果你主要阅读英文：禁用翻译
- 如果需要中文摘要：仅翻译高分文章（score >= 75）
- 初期测试：可以完全禁用节省成本

### Q5: 使用 Gemini 还是 GPT？

**推荐方案**:
```json
"analysis": {
  "model": "gemini-2.0-flash-exp",     // 主力模型（成本低）
  "backup_model": "gpt-4o-mini"         // 备用模型
}
```

**对比**:
| 模型 | 成本 | 速度 | 质量 | 建议 |
|------|------|------|------|------|
| Gemini 2.0 Flash | 极低 | 极快 | 高 | ⭐ 测试和日常使用 |
| GPT-4o-mini | 低 | 快 | 高 | 备用 |
| GPT-4o | 中 | 中 | 极高 | 仅精选文章 |

---

## 📈 下一步优化

测试成功后（1-2周），可以：

### 扩展 RSS 源
从 `rss_sources_for_ai_students.json` 中添加更多源：
- 增加 arXiv 论文源（cs.LG, cs.CL, cs.CV）
- 增加个人博客（Sebastian Ruder, The Gradient）
- 增加实验室博客（BAIR, ML@CMU）

### 开发前端界面
简单的阅读界面：
- 文章列表（按评分/日期排序）
- 领域筛选
- 标签云
- 收藏功能

### 自动推送
每日/每周摘要：
- 邮件推送前 5 篇高分文章
- Telegram/微信机器人通知
- RSS 输出（供自己订阅）

### 数据分析
- 各源的平均评分
- 热门领域统计
- 标签频率分析

---

## 🆚 与 BestBlogs.dev 的区别

| 维度 | BestBlogs.dev | 你的AI学生系统 |
|------|---------------|----------------|
| **RSS源** | 400个（多领域） | 25个（AI专属） |
| **内容类型** | 文章+播客+视频+推文 | 仅文章 |
| **目标受众** | 泛技术人群 | AI/ML学生 |
| **领域分类** | 4大类 | 6大AI子领域 |
| **评分侧重** | 内容深度+相关性 | 学术价值+实践价值 |
| **后端实现** | 复杂（Java等） | 简化（Python+Dify） |
| **部署** | 线上服务 | 本地/个人使用 |

---

## 📝 总结

你现在有了：
1. ✅ **测试配置文件** - `test_ai_student_config.json`（7个精选源）
2. ✅ **集成指南** - 本文档（完整流程）
3. ✅ **工作流参数** - Dify 配置建议
4. ✅ **数据库设计** - SQLite 表结构
5. ✅ **示例代码** - RSS爬虫和Dify调用

**建议测试流程**:
1. 先手动测试 1-2 个RSS源
2. 在 Dify 中导入并调整工作流
3. 验证完整流程（抓取→初评→分析→存储）
4. 逐步启用更多源
5. 根据实际使用调整参数

有任何问题随时问我！🚀
