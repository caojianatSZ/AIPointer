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
