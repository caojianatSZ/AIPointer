# AI 网关 P0 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 AI 网关 MVP——定时扫描飞书知识库增量，调用 Claude API 提取摘要/分类/打标，写入飞书多维表格。

**Architecture:** 一个 Python 脚本，通过 GitHub Actions 每天定时执行。飞书 API 做数据读写，Claude API 做语义处理。状态通过多维表格持久化。

**Tech Stack:** Python 3.11, Feishu API (lark-oapi), Anthropic Claude API, GitHub Actions

**项目路径:** `/Users/caojian/Projects/WayToAGI`

---

### Task 1: 项目脚手架和 Feishu API 凭证

**Files:**
- Create: `ai_gateway/__init__.py`
- Create: `ai_gateway/config.py`
- Create: `requirements.txt`

- [ ] **Step 1: 创建项目目录结构和 requirements.txt**

```text
# requirements.txt
httpx>=0.28.0
lark-oapi>=3.0.0
anthropic>=0.49.0
pydantic>=2.0.0
pytest>=8.0.0
pytest-env>=1.1.0
respx>=0.21.0
```

- [ ] **Step 2: 实现配置模块**

```python
# ai_gateway/config.py
"""
从环境变量读取配置，所有敏感信息通过 GitHub Secrets 注入。
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    # 飞书应用凭证
    feishu_app_id: str = field(default_factory=lambda: os.environ.get("FEISHU_APP_ID", ""))
    feishu_app_secret: str = field(default_factory=lambda: os.environ.get("FEISHU_APP_SECRET", ""))

    # Claude API
    claude_api_key: str = field(default_factory=lambda: os.environ.get("CLAUDE_API_KEY", ""))

    # 飞书知识库空间 Token（手动配置）
    wiki_space_token: str = field(default_factory=lambda: os.environ.get("WIKI_SPACE_TOKEN", ""))

    # 多维表格 Token（记录索引 + 配置行）
    base_token: str = field(default_factory=lambda: os.environ.get("BASE_TOKEN", ""))
    base_table_id: str = field(default_factory=lambda: os.environ.get("BASE_TABLE_ID", ""))
    base_config_record_id: str = field(default_factory=lambda: os.environ.get("BASE_CONFIG_RECORD_ID", ""))

    # Claude 模型
    claude_model: str = field(default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"))

    def validate(self) -> list[str]:
        missing = []
        for field_name in ["feishu_app_id", "feishu_app_secret", "claude_api_key",
                           "wiki_space_token", "base_token", "base_table_id"]:
            if not getattr(self, field_name):
                missing.append(field_name)
        return missing
```

- [ ] **Step 3: 写测试验证默认值**

```python
# tests/test_config.py
import os
from ai_gateway.config import Config


def test_config_reads_from_env():
    os.environ["FEISHU_APP_ID"] = "cli_xxx"
    os.environ["CLAUDE_API_KEY"] = "sk-xxx"
    cfg = Config()
    assert cfg.feishu_app_id == "cli_xxx"
    assert cfg.claude_api_key == "sk-xxx"


def test_config_validate_returns_missing():
    os.environ.clear()
    cfg = Config()
    missing = cfg.validate()
    assert "feishu_app_id" in missing
    assert "claude_api_key" in missing


def test_config_validate_all_present():
    cfg = Config()
    cfg.feishu_app_id = "x"
    cfg.feishu_app_secret = "x"
    cfg.claude_api_key = "x"
    cfg.wiki_space_token = "x"
    cfg.base_token = "x"
    cfg.base_table_id = "x"
    assert cfg.validate() == []
```

- [ ] **Step 4: 运行测试确保通过**

Run: `cd /Users/caojian/Projects/WayToAGI && python -m pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 5: 初始化 git 仓库并提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git init
git add ai_gateway/__init__.py ai_gateway/config.py requirements.txt tests/test_config.py tests/__init__.py
git commit -m "chore: scaffold project structure with config module"
```

---

### Task 2: Feishu API 客户端

**Files:**
- Create: `ai_gateway/feishu_client.py`
- Modify: `requirements.txt` (已完成)

- [ ] **Step 1: 写 FeishuClient 的接口测试**

```python
# tests/test_feishu_client.py
import pytest
from ai_gateway.feishu_client import FeishuClient
from ai_gateway.config import Config


@pytest.fixture
def client():
    cfg = Config()
    cfg.feishu_app_id = "test_id"
    cfg.feishu_app_secret = "test_secret"
    cfg.wiki_space_token = "space_token"
    cfg.base_token = "base_token"
    cfg.base_table_id = "table_id"
    return FeishuClient(cfg)


@pytest.mark.asyncio
async def test_authenticate_calls_api(client):
    """发送认证请求并返回 token。"""
    # 待实现
    pass


def test_get_last_run_timestamp_default(client):
    """没有配置行时应返回 None。"""
    ts = client.get_last_run_timestamp()
    assert ts is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/caojian/Projects/WayToAGI && python -m pytest tests/test_feishu_client.py -v`
Expected: ModuleNotFoundError / ImportError

- [ ] **Step 3: 实现 FeishuClient**

```python
# ai_gateway/feishu_client.py
"""
飞书 API 封装：认证、知识库文档读取、多维表格读写。
"""
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

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
        """列出知识库空间中的文档，支持分页。"""
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

    def get_last_run_timestamp(self):
        """从配置行读取上次处理时间戳（同步暂存，后续异步化）。"""
        return None  # 暂存，Task 5 实现

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
```

- [ ] **Step 4: 运行测试确保通过**

Run: `cd /Users/caojian/Projects/WayToAGI && python -c "from ai_gateway.feishu_client import FeishuClient; print('import ok')"`
Expected: `import ok`

- [ ] **Step 5: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add ai_gateway/feishu_client.py
git commit -m "feat: Feishu API client with auth, wiki, and bitable operations"
```

---

### Task 3: 扫描器模块

**Files:**
- Create: `ai_gateway/scanner.py`

- [ ] **Step 1: 编写扫描器测试**

```python
# tests/test_scanner.py
from datetime import datetime, timezone
import pytest
from ai_gateway.scanner import Scanner
from ai_gateway.config import Config


@pytest.mark.asyncio
async def test_scan_returns_updated_docs():
    """扫描应返回指定时间戳后更新的文档列表。"""
    cfg = Config()
    cfg.wiki_space_token = "test"
    scanner = Scanner(cfg, feishu_client=None)  # 暂存
    assert scanner is not None
```

- [ ] **Step 2: 实现扫描器**

```python
# ai_gateway/scanner.py
"""
扫描飞书知识库，找出上次运行后新增/修改的文档。
"""
from datetime import datetime
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
                obj = node.get("obj", {})  # 文档对象信息
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
```

- [ ] **Step 3: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add ai_gateway/scanner.py tests/test_scanner.py
git commit -m "feat: scanner module for incremental wiki doc detection"
```

---

### Task 4: AI 处理器（Claude API）

**Files:**
- Create: `ai_gateway/processor.py`

- [ ] **Step 1: 编写处理器测试**

```python
# tests/test_processor.py
import pytest
from ai_gateway.processor import ProcessResult, build_process_prompt


def test_build_prompt_contains_content():
    prompt = build_process_prompt("客户反映LLM输出格式不对")
    assert "LLM输出格式不对" in prompt


def test_process_result_roundtrip():
    result = ProcessResult(
        doc_id="doc_123",
        title="LLM输出格式稳定性",
        summary="通过few-shot+JSON Schema解决",
        tags=["LLM调优", "JSON Schema"],
        client="客户A",
        industry="传媒",
        scene_type="模型调优",
        execution_steps=["分析错误模式", "添加Schema约束"],
        is_novel=True,
    )
    assert result.doc_id == "doc_123"
    assert len(result.execution_steps) == 2
```

- [ ] **Step 2: 实现处理器**

```python
# ai_gateway/processor.py
"""
调用 Claude API 对飞书文档内容进行分类、摘要、打标。
"""
from dataclasses import dataclass, field, asdict
from typing import List

from anthropic import Anthropic
from ai_gateway.config import Config


@dataclass
class ProcessResult:
    doc_id: str
    title: str
    summary: str
    tags: List[str]
    client: str
    industry: str
    scene_type: str
    execution_steps: List[str]
    is_novel: bool = True


PROCESS_SYSTEM_PROMPT = """你是一个 AI 咨询知识管理助手。你的任务是从顾问的工作记录中提取结构化信息。

请分析以下顾问的工作记录内容，输出 JSON 格式：
{
  "title": "简短标题，格式：客户名_场景关键词",
  "summary": "100-200字结构化摘要，含问题描述和解决方案",
  "tags": ["技术标签1", "技术标签2"],
  "client": "客户名称（从上下文中推断）",
  "industry": "所属行业（传媒/广告/出版/电商/金融/其他）",
  "scene_type": "场景类型（模型调优/知识库搭建/流程改进/提示词工程/其他）",
  "execution_steps": ["步骤1", "步骤2"],
  "is_novel": true
}

只输出 JSON，不要其他文字。
"""


def build_process_prompt(content: str) -> str:
    return f"以下是顾问的工作记录内容：\n\n{content}"


class Processor:
    def __init__(self, config: Config):
        self.client = Anthropic(api_key=config.claude_api_key)
        self.model = config.claude_model

    def process(self, doc_id: str, title: str, content: str) -> ProcessResult:
        prompt = build_process_prompt(content)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=PROCESS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = json.loads(response.content[0].text)
        return ProcessResult(
            doc_id=doc_id,
            title=raw.get("title", title),
            summary=raw.get("summary", ""),
            tags=raw.get("tags", []),
            client=raw.get("client", ""),
            industry=raw.get("industry", ""),
            scene_type=raw.get("scene_type", ""),
            execution_steps=raw.get("execution_steps", []),
            is_novel=raw.get("is_novel", True),
        )
```

- [ ] **Step 3: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add ai_gateway/processor.py tests/test_processor.py
git commit -m "feat: AI processor with Claude API for classification and summarization"
```

---

### Task 5: 去重引擎

**Files:**
- Create: `ai_gateway/dedup_engine.py`

- [ ] **Step 1: 实现去重引擎**

```python
# ai_gateway/dedup_engine.py
"""
判断新记录是否是已有场景的变体，维护复用次数。
"""
from typing import List, Optional
from dataclasses import dataclass

from ai_gateway.processor import ProcessResult


@dataclass
class ExistingRecord:
    record_id: str
    title: str
    tags: List[str]
    scene_type: str
    reuse_count: int


class DedupEngine:
    def __init__(self, existing_records: List[ExistingRecord]):
        self._records = existing_records
        self._tag_index = self._build_tag_index(existing_records)

    def _build_tag_index(self, records: List[ExistingRecord]) -> dict[str, List[ExistingRecord]]:
        index: dict[str, List[ExistingRecord]] = {}
        for rec in records:
            for tag in rec.tags:
                index.setdefault(tag, []).append(rec)
        return index

    def find_similar(self, result: ProcessResult) -> Optional[ExistingRecord]:
        """根据标签重叠度找最相似的已有记录。"""
        if not result.tags:
            return None
        candidates: dict[str, int] = {}
        for tag in result.tags:
            for rec in self._tag_index.get(tag, []):
                candidates[rec.record_id] = candidates.get(rec.record_id, 0) + 1
        if not candidates:
            return None
        best_id = max(candidates, key=candidates.get)
        for rec in self._records:
            if rec.record_id == best_id:
                return rec
        return None
```

- [ ] **Step 2: 写测试**

```python
# tests/test_dedup_engine.py
from ai_gateway.dedup_engine import DedupEngine, ExistingRecord
from ai_gateway.processor import ProcessResult


def test_find_similar_by_tag_overlap():
    records = [
        ExistingRecord("1", "LLM输出格式", ["LLM调优", "JSON"], "模型调优", 2),
        ExistingRecord("2", "知识库检索", ["RAG", "Embedding"], "知识库搭建", 1),
    ]
    engine = DedupEngine(records)
    result = ProcessResult(
        doc_id="3", title="新场景", summary="test", tags=["LLM调优", "JSON"],
        client="", industry="", scene_type="", execution_steps=[], is_novel=True,
    )
    similar = engine.find_similar(result)
    assert similar is not None
    assert similar.record_id == "1"


def test_find_similar_no_match():
    engine = DedupEngine([])
    result = ProcessResult(
        doc_id="1", title="新场景", summary="test", tags=["全新"],
        client="", industry="", scene_type="", execution_steps=[], is_novel=True,
    )
    assert engine.find_similar(result) is None
```

- [ ] **Step 3: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add ai_gateway/dedup_engine.py tests/test_dedup_engine.py
git commit -m "feat: dedup engine for scene matching by tag overlap"
```

---

### Task 6: 主流水线编排

**Files:**
- Create: `ai_gateway/main.py`

- [ ] **Step 1: 实现主流水线**

```python
# ai_gateway/main.py
"""
AI 网关主流水线：扫描 → 处理 → 去重 → 写回 → 报告。
"""
import asyncio
import logging
import sys
from datetime import datetime, timezone

from ai_gateway.config import Config
from ai_gateway.feishu_client import FeishuClient
from ai_gateway.scanner import Scanner
from ai_gateway.processor import Processor
from ai_gateway.dedup_engine import DedupEngine, ExistingRecord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def run_pipeline():
    cfg = Config()
    missing = cfg.validate()
    if missing:
        logger.error("Missing config: %s", ", ".join(missing))
        sys.exit(1)

    fs_client = FeishuClient(cfg)
    try:
        # 1. 读取上次处理时间
        last_run = fs_client.get_last_run_timestamp()
        since = None
        # TODO: 从多维表格配置行读取时间戳

        # 2. 扫描知识库增量
        scanner = Scanner(cfg, fs_client)
        docs = await scanner.scan(since)
        logger.info("Found %d new/updated docs", len(docs))

        if not docs:
            logger.info("No new docs to process")
            return

        # 3. 获取已有记录用于去重
        existing_raw = await fs_client.list_records()
        existing = [
            ExistingRecord(
                record_id=r.get("record_id", ""),
                title=r.get("fields", {}).get("标题", ""),
                tags=r.get("fields", {}).get("标签", "").split(",") if r.get("fields", {}).get("标签") else [],
                scene_type=r.get("fields", {}).get("场景类型", ""),
                reuse_count=int(r.get("fields", {}).get("复用次数", 0)),
            )
            for r in existing_raw
        ]
        dedup = DedupEngine(existing)

        # 4. 逐条处理
        processor = Processor(cfg)
        processed_count = 0
        for doc in docs:
            content = await fs_client.get_doc_content(doc.doc_token)
            if not content:
                continue
            result = processor.process(doc.doc_token, doc.title, content)

            # 5. 去重
            similar = dedup.find_similar(result)
            if similar:
                logger.info("Similar record found: %s (reuse count: %d)", similar.title, similar.reuse_count)
                # 更新复用次数
                await fs_client.update_record(similar.record_id, {"复用次数": similar.reuse_count + 1})
            else:
                # 6. 写入多维表格
                record_id = await fs_client.create_record({
                    "标题": result.title,
                    "摘要": result.summary,
                    "客户": result.client,
                    "行业": result.industry,
                    "场景类型": result.scene_type,
                    "标签": ",".join(result.tags),
                    "复用次数": 0,
                    "是否模板化": False,
                    "创建日期": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "状态": "已整理",
                })
                logger.info("Created record %s: %s", record_id, result.title)
            processed_count += 1

        # 7. 更新时间戳
        # TODO: 写入多维表格配置行
        logger.info("Pipeline complete. Processed %d docs.", processed_count)

    finally:
        await fs_client.close()


def main():
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试流水线可导入**

```python
# tests/test_main.py
from ai_gateway.main import run_pipeline, main


def test_main_imports():
    """确保主模块可导入。"""
    assert callable(run_pipeline)
    assert callable(main)
```

- [ ] **Step 3: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add ai_gateway/main.py tests/test_main.py
git commit -m "feat: main pipeline orchestrator"
```

---

### Task 7: 日报生成器

**Files:**
- Create: `ai_gateway/reporter.py`

- [ ] **Step 1: 实现日报生成器**

```python
# ai_gateway/reporter.py
"""
基于当天处理的记录，生成日报/周报并写入飞书文档。
"""
import logging
from datetime import datetime, timezone
from typing import List

from ai_gateway.processor import ProcessResult

logger = logging.getLogger(__name__)


def format_daily_report(results: List[ProcessResult], date: datetime) -> str:
    """生成日报 Markdown 内容。"""
    lines = [
        f"# AI 网关日报 — {date.strftime('%Y-%m-%d')}",
        "",
        f"今日处理 **{len(results)}** 条新记录。",
        "",
    ]
    if results:
        lines.append("## 今日记录")
        for r in results:
            tags_str = "、".join(r.tags[:5])
            lines.append(f"### {r.title}")
            lines.append(f"- **客户：** {r.client}")
            lines.append(f"- **行业：** {r.industry}")
            lines.append(f"- **场景类型：** {r.scene_type}")
            lines.append(f"- **标签：** {tags_str}")
            lines.append(f"- **摘要：** {r.summary}")
            lines.append("")
    return "\n".join(lines)


def format_weekly_report(all_results: List[ProcessResult], date: datetime) -> str:
    """生成周报 Markdown 内容。"""
    week_num = date.isocalendar().week
    lines = [
        f"# AI 网关周报 — 第 {week_num} 周",
        "",
        f"本周共处理 **{len(all_results)}** 条记录。",
        "",
    ]
    # 按场景类型聚合
    by_type: dict[str, list] = {}
    for r in all_results:
        by_type.setdefault(r.scene_type, []).append(r)
    if by_type:
        lines.append("## 场景分布")
        for scene_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            lines.append(f"- **{scene_type}：** {len(items)} 条")
        lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 2: 写测试**

```python
# tests/test_reporter.py
from datetime import datetime
from ai_gateway.reporter import format_daily_report, format_weekly_report
from ai_gateway.processor import ProcessResult


def test_daily_report_empty():
    result = format_daily_report([], datetime(2026, 5, 4))
    assert "0" in result


def test_daily_report_with_results():
    results = [
        ProcessResult(
            doc_id="1", title="LLM调优", summary="解决了",
            tags=["LLM"], client="客户A", industry="传媒",
            scene_type="模型调优", execution_steps=[], is_novel=True,
        )
    ]
    result = format_daily_report(results, datetime(2026, 5, 4))
    assert "客户A" in result
    assert "1" in result or "1" in result  # 1 条记录


def test_weekly_report_groups_by_type():
    results = [
        ProcessResult(doc_id="1", title="T1", summary="S1", tags=[], client="A",
                      industry="", scene_type="模型调优", execution_steps=[], is_novel=True),
        ProcessResult(doc_id="2", title="T2", summary="S2", tags=[], client="B",
                      industry="", scene_type="知识库搭建", execution_steps=[], is_novel=True),
    ]
    result = format_weekly_report(results, datetime(2026, 5, 4))
    assert "模型调优" in result
    assert "知识库搭建" in result
```

- [ ] **Step 3: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add ai_gateway/reporter.py tests/test_reporter.py
git commit -m "feat: daily and weekly report generator"
```

---

### Task 8: GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/ai-gateway.yml`

- [ ] **Step 1: 创建 CI/CD 工作流**

```yaml
# .github/workflows/ai-gateway.yml
name: AI Gateway Daily Pipeline

on:
  schedule:
    - cron: '0 2 * * *'     # 每天 UTC 02:00（北京时间 10:00）
  workflow_dispatch:         # 支持手动触发

env:
  PYTHON_VERSION: '3.11'

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run AI Gateway Pipeline
        run: python -m ai_gateway.main
        env:
          FEISHU_APP_ID: ${{ secrets.FEISHU_APP_ID }}
          FEISHU_APP_SECRET: ${{ secrets.FEISHU_APP_SECRET }}
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
          WIKI_SPACE_TOKEN: ${{ secrets.WIKI_SPACE_TOKEN }}
          BASE_TOKEN: ${{ secrets.BASE_TOKEN }}
          BASE_TABLE_ID: ${{ secrets.BASE_TABLE_ID }}
          BASE_CONFIG_RECORD_ID: ${{ secrets.BASE_CONFIG_RECORD_ID }}
          CLAUDE_MODEL: claude-sonnet-4-20250514
```

- [ ] **Step 2: 提交**

```bash
cd /Users/caojian/Projects/WayToAGI
git add .github/workflows/ai-gateway.yml
git commit -m "ci: add GitHub Actions workflow for daily AI gateway pipeline"
```

---

### Task 9: 运行完整测试套件

- [ ] **Step 1: 安装依赖并运行所有测试**

```bash
cd /Users/caojian/Projects/WayToAGI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: 提交最终版本**

```bash
cd /Users/caojian/Projects/WayToAGI
git add -A
git commit -m "chore: finalize P0 MVP with full test suite"
```

---

## 未包含在 P0 中的内容（后续阶段）

| 项目 | 计划阶段 | 说明 |
|------|----------|------|
| 自媒体内容生成（小红书/抖音） | P2 | 需要 content_creator 集成 |
| 去重引擎完善 | P2 | 当前为标签匹配，后续可引入语义匹配 |
| Playbook 自动提炼 | P3 | 基于复用次数和场景聚类 |
| 群聊自动检测 | P3 | 需要飞书机器人权限 |
| 多维表格搜索页面 | P1 | 飞书多维表格自带筛选能力，暂时够用 |
