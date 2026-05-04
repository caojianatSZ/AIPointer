"""
扫描飞书知识库，找出上次运行后新增/修改的文档。
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from ai_gateway.config import Config


@dataclass
class DocInfo:
    doc_token: str
    title: str
    updated_time: datetime


class Scanner:
    def __init__(self, config: Config, feishu_client):
        self.config = config
        self.client = feishu_client

    async def scan(self, since: Optional[datetime] = None) -> List[DocInfo]:
        """
        扫描知识库中所有节点，返回 updated_time > since 的文档列表。
        since 为 None 时返回所有文档（首次运行）。
        """
        docs = []
        page_token = None
        while True:
            result = await self.client.list_wiki_docs(page_token)
            data = result.get("data", {})
            for item in data.get("items", []):
                node = item.get("node", {})
                obj = node.get("obj", {})
                updated_str = obj.get("update_time", "")
                if not updated_str:
                    continue
                updated = datetime.fromtimestamp(int(updated_str), tz=timezone.utc)
                if since is None or updated > since:
                    docs.append(DocInfo(
                        doc_token=obj.get("token", ""),
                        title=obj.get("title", ""),
                        updated_time=updated,
                    ))
            page_token = data.get("page_token")
            if not page_token:
                break
        return docs
