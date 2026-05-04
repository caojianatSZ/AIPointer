import os
from ai_gateway.config import Config


def test_config_reads_from_env():
    os.environ["FEISHU_APP_ID"] = "cli_xxx"
    os.environ["CLAUDE_API_KEY"] = "sk-xxx"
    cfg = Config()
    assert cfg.feishu_app_id == "cli_xxx"
    assert cfg.claude_api_key == "sk-xxx"
    # 清理环境变量以免影响其他测试
    del os.environ["FEISHU_APP_ID"]
    del os.environ["CLAUDE_API_KEY"]


def test_config_validate_returns_missing():
    # 确保关键环境变量不存在
    for key in ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "CLAUDE_API_KEY",
                "WIKI_SPACE_TOKEN", "BASE_TOKEN", "BASE_TABLE_ID"]:
        os.environ.pop(key, None)
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
