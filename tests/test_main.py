# tests/test_main.py
from ai_gateway.main import run_pipeline, main


def test_main_imports():
    """确保主模块可导入。"""
    assert callable(run_pipeline)
    assert callable(main)
