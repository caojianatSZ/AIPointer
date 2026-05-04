import pytest
from ai_gateway.feishu_client import FeishuClient
from ai_gateway.config import Config


def test_client_init():
    cfg = Config()
    cfg.feishu_app_id = "test_id"
    cfg.feishu_app_secret = "test_secret"
    cfg.wiki_space_token = "space_token"
    cfg.base_token = "base_token"
    cfg.base_table_id = "table_id"
    client = FeishuClient(cfg)
    assert client._BASE_URL == "https://open.feishu.cn/open-apis"
    assert client.config.feishu_app_id == "test_id"


def test_client_methods_exist():
    cfg = Config()
    client = FeishuClient(cfg)
    assert hasattr(client, "list_wiki_docs")
    assert hasattr(client, "get_doc_content")
    assert hasattr(client, "list_records")
    assert hasattr(client, "create_record")
    assert hasattr(client, "update_record")
    assert hasattr(client, "close")
