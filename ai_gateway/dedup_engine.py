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
