import pytest
from datetime import datetime, timezone
from ai_gateway.scanner import Scanner, DocInfo
from ai_gateway.config import Config


def test_docinfo_dataclass():
    dt = datetime.now(timezone.utc)
    info = DocInfo(doc_token="token123", title="Test Doc", updated_time=dt)
    assert info.doc_token == "token123"
    assert info.title == "Test Doc"
    assert info.updated_time == dt


def test_scanner_init():
    cfg = Config()
    scanner = Scanner(cfg, feishu_client=None)
    assert scanner.config == cfg
    assert scanner.client is None
