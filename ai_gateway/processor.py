"""
调用 Claude API 对飞书文档内容进行分类、摘要、打标。
"""
from dataclasses import dataclass, field, asdict
from typing import List

from anthropic import Anthropic
from ai_gateway.config import Config


@dataclass
class ProcessResult:
    doc_id: str
    title: str
    summary: str
    tags: List[str]
    client: str
    industry: str
    scene_type: str
    execution_steps: List[str]
    is_novel: bool = True


PROCESS_SYSTEM_PROMPT = """你是一个 AI 咨询知识管理助手。你的任务是从顾问的工作记录中提取结构化信息。

请分析以下顾问的工作记录内容，输出 JSON 格式：
{
  "title": "简短标题，格式：客户名_场景关键词",
  "summary": "100-200字结构化摘要，含问题描述和解决方案",
  "tags": ["技术标签1", "技术标签2"],
  "client": "客户名称（从上下文中推断）",
  "industry": "所属行业（传媒/广告/出版/电商/金融/其他）",
  "scene_type": "场景类型（模型调优/知识库搭建/流程改进/提示词工程/其他）",
  "execution_steps": ["步骤1", "步骤2"],
  "is_novel": true
}

只输出 JSON，不要其他文字。
"""


def build_process_prompt(content: str) -> str:
    return f"以下是顾问的工作记录内容：\n\n{content}"


class Processor:
    def __init__(self, config: Config):
        self.client = Anthropic(api_key=config.claude_api_key)
        self.model = config.claude_model

    def process(self, doc_id: str, title: str, content: str) -> ProcessResult:
        prompt = build_process_prompt(content)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=PROCESS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = json.loads(response.content[0].text)
        return ProcessResult(
            doc_id=doc_id,
            title=raw.get("title", title),
            summary=raw.get("summary", ""),
            tags=raw.get("tags", []),
            client=raw.get("client", ""),
            industry=raw.get("industry", ""),
            scene_type=raw.get("scene_type", ""),
            execution_steps=raw.get("execution_steps", []),
            is_novel=raw.get("is_novel", True),
        )
