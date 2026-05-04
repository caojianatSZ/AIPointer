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
