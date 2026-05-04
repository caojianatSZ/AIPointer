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
    assert result.client == "客户A"
    assert result.industry == "传媒"
    assert result.is_novel is True


def test_process_result_defaults():
    """测试 is_novel 默认值为 True。"""
    result = ProcessResult(
        doc_id="1", title="T", summary="S", tags=[], client="",
        industry="", scene_type="", execution_steps=[],
    )
    assert result.is_novel is True
