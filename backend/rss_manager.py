"""
RSS 源管理模块
负责：从 OPML 导入、添加/删除源、启用/禁用源
"""

import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from models import RSSSource
from typing import List, Dict
import os


class RSSSourceManager:
    """RSS 源管理器"""

    def __init__(self, db: Session):
        self.db = db

    def import_from_opml(self, opml_file_path: str) -> Dict[str, int]:
        """
        从 OPML 文件导入 RSS 源

        Args:
            opml_file_path: OPML 文件路径

        Returns:
            导入统计 {"total": 总数, "new": 新增数, "existing": 已存在数}
        """
        if not os.path.exists(opml_file_path):
            raise FileNotFoundError(f"OPML file not found: {opml_file_path}")

        tree = ET.parse(opml_file_path)
        root = tree.getroot()

        total = 0
        new = 0
        existing = 0

        # 查找所有 outline 元素
        for outline in root.findall(".//outline[@type='rss']"):
            total += 1
            name = outline.get("text", "")
            title = outline.get("title", name)
            rss_url = outline.get("xmlUrl", "")

            if not rss_url:
                continue

            # 检查是否已存在
            exists = self.db.query(RSSSource).filter(
                RSSSource.rss_url == rss_url
            ).first()

            if exists:
                existing += 1
                continue

            # 创建新源
            source = RSSSource(
                name=name,
                title=title,
                rss_url=rss_url,
                category=self._categorize_source(name),
                language=self._detect_language(name)
            )

            self.db.add(source)
            new += 1

        self.db.commit()

        return {
            "total": total,
            "new": new,
            "existing": existing
        }

    def add_source(self, name: str, rss_url: str, category: str = None,
                   language: str = "zh_CN") -> RSSSource:
        """手动添加单个 RSS 源"""

        # 检查是否已存在
        exists = self.db.query(RSSSource).filter(
            RSSSource.rss_url == rss_url
        ).first()

        if exists:
            raise ValueError(f"RSS source already exists: {rss_url}")

        source = RSSSource(
            name=name,
            title=name,
            rss_url=rss_url,
            category=category or self._categorize_source(name),
            language=language
        )

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        return source

    def list_sources(self, enabled_only: bool = False) -> List[RSSSource]:
        """列出所有 RSS 源"""
        query = self.db.query(RSSSource)

        if enabled_only:
            query = query.filter(RSSSource.enabled == True)

        return query.all()

    def enable_source(self, source_id: int):
        """启用 RSS 源"""
        source = self.db.query(RSSSource).filter(RSSSource.id == source_id).first()
        if source:
            source.enabled = True
            self.db.commit()

    def disable_source(self, source_id: int):
        """禁用 RSS 源"""
        source = self.db.query(RSSSource).filter(RSSSource.id == source_id).first()
        if source:
            source.enabled = False
            self.db.commit()

    def delete_source(self, source_id: int):
        """删除 RSS 源"""
        source = self.db.query(RSSSource).filter(RSSSource.id == source_id).first()
        if source:
            self.db.delete(source)
            self.db.commit()

    def _categorize_source(self, name: str) -> str:
        """根据源名称自动分类"""
        name_lower = name.lower()

        ai_keywords = ["ai", "deepmind", "openai", "machine learning", "llm", "gpt",
                       "人工智能", "机器学习", "深度学习", "智能"]
        tech_keywords = ["engineering", "tech", "developer", "技术", "开发"]
        product_keywords = ["product", "ux", "design", "产品", "设计"]

        for keyword in ai_keywords:
            if keyword in name_lower:
                return "Artificial_Intelligence"

        for keyword in product_keywords:
            if keyword in name_lower:
                return "Product_Development"

        for keyword in tech_keywords:
            if keyword in name_lower:
                return "Programming_Technology"

        return "Programming_Technology"  # 默认分类

    def _detect_language(self, name: str) -> str:
        """检测语言"""
        # 简单检测：如果包含中文字符，则为中文
        for char in name:
            if '\u4e00' <= char <= '\u9fff':
                return "zh_CN"
        return "en_US"
