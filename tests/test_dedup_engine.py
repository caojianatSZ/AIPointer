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


def test_find_similar_empty_tags():
    records = [ExistingRecord("1", "LLM", ["tag"], "type", 0)]
    engine = DedupEngine(records)
    result = ProcessResult(
        doc_id="2", title="T", summary="S", tags=[],
        client="", industry="", scene_type="", execution_steps=[], is_novel=True,
    )
    assert engine.find_similar(result) is None
