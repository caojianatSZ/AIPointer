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
    assert "1" in result


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
