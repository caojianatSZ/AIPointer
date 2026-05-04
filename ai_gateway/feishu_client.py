"""
飞书 API 封装：认证、知识库文档读取、多维表格读写。
"""
import time
from datetime import datetime
from typing import Optional

import httpx

from ai_gateway.config import Config


class FeishuClient:
    _BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, config: Config):
        self.config = config
        self._client = httpx.AsyncClient(base_url=self._BASE_URL, timeout=30)
        self._tenant_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def close(self):
        await self._client.aclose()

    async def _ensure_token(self) -> str:
        if self._tenant_token and time.time() < self._token_expires_at:
            return self._tenant_token
        resp = await self._client.post(
            "/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.config.feishu_app_id,
                "app_secret": self.config.feishu_app_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._tenant_token = data["tenant_access_token"]
        self._token_expires_at = time.time() + data.get("expire", 7200) - 60
        return self._tenant_token

    async def _request(self, method: str, path: str, **kwargs):
        token = await self._ensure_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return await self._client.request(method, path, headers=headers, **kwargs)

    # ── 知识库 ──

    async def list_wiki_docs(self, page_token: Optional[str] = None) -> dict:
        """列出知识库空间中的文档节点，支持分页。"""
        params = {"page_size": 50}
        if page_token:
            params["page_token"] = page_token
        resp = await self._request(
            "GET",
            f"/wiki/v2/spaces/{self.config.wiki_space_token}/nodes",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_doc_content(self, doc_token: str) -> str:
        """获取飞书文档的纯文本内容。"""
        resp = await self._request(
            "GET",
            f"/docx/v1/documents/{doc_token}/raw_content",
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("content", "")

    # ── 多维表格 ──

    async def list_records(self, page_token: Optional[str] = None) -> list[dict]:
        """列出多维表格中所有记录。"""
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        resp = await self._request(
            "GET",
            f"/bitable/v1/apps/{self.config.base_token}/tables/{self.config.base_table_id}/records",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("items", [])

    async def create_record(self, fields: dict) -> str:
        """在多维表格中创建一条记录，返回记录 ID。"""
        resp = await self._request(
            "POST",
            f"/bitable/v1/apps/{self.config.base_token}/tables/{self.config.base_table_id}/records",
            json={"fields": fields},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("record", {}).get("record_id", "")

    async def update_record(self, record_id: str, fields: dict):
        """更新多维表格中的一条记录。"""
        resp = await self._request(
            "PUT",
            f"/bitable/v1/apps/{self.config.base_token}/tables/{self.config.base_table_id}/records/{record_id}",
            json={"fields": fields},
        )
        resp.raise_for_status()
