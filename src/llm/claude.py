import json
import re
from anthropic import Anthropic
from src.sources import NewsItem
from src.config import Config

SYSTEM_PROMPT = """你是一个 AI 科技新闻编辑，擅长用中文撰写高质量的技术周报。
要求：
- 用简洁、专业的中文写摘要，每条 50-100 字，包含具体的技术亮点或影响
- 保持客观，不添加评论或预测
- 英文专有名词保留原文（如 GPT-4o、Claude Sonnet 4）
- 按重要性排序，优先保留有明确信息来源和具体细节的新闻
- 每个专栏最多 5 条，宁缺毋滥"""


def _build_prompt(items: list[NewsItem], max_per_cat: int) -> str:
    news_lines = []
    for i, item in enumerate(items):
        desc = (item.description or "")[:400].replace("\n", " ")
        news_lines.append(
            f"[{i+1}] {item.title}\n"
            f"    来源: {item.source_name} | 链接: {item.url}\n"
            f"    摘要: {desc}\n"
        )

    news_text = "\n".join(news_lines)

    return f"""分析以下本周 AI 新闻，整理成结构化中文周报。

内容分为两大板块：

**板块一：AI 科技资讯**
包含子专栏（按实际情况动态出现，无内容则不显示）：
- 新模型发布 — 新 AI 模型、LLM 发布、开源模型
- 产品功能更新 — ChatGPT/Claude/Gemini 等产品更新
- AI 工具推荐 — 新的 AI 应用和开发工具
- 行业动态 — 收购、合作、融资、人事调整

**板块二：AI 安全技术洞察**
子专栏根据实际内容动态命名（如：安全研究、红队测试、监管政策、对齐研究等），
不要用固定的专栏名，按本周实际安全类新闻的主题来创建。

要求：
- 每条新闻写 50-100 字中文描述，包含具体技术细节、数据或影响
- 合并来自不同源的重复报道（保留信息最完整的版本）
- 子专栏有内容才显示，无内容就整个省略
- 删除不相关或价值低的内容
- 每个子专栏最多 {max_per_cat} 条
- 只输出 JSON，不要其他内容

输出 JSON 格式：
{{"overview": "本周概览（2-3句话中文概述本周最重要的 AI 动态）",
"sections": [
  {{"name": "AI 科技资讯",
    "columns": [
      {{"name": "新模型发布",
        "items": [
          {{"title": "原标题或中文翻译",
           "summary": "50-100字中文描述，包含具体技术细节和影响",
           "url": "原文链接",
           "source": "来源名称"}}
        ]}}
    ]}},
  {{"name": "AI 安全技术洞察",
    "columns": [
      {{"name": "Claude根据内容动态命名的专栏名",
        "items": [...]}}
    ]}}
]}}

以下是本周 AI 新闻：
{news_text}"""


def refine(config: Config, items: list[NewsItem]) -> dict:
    if not items:
        return {
            "overview": "本周未收集到足够的 AI 新闻数据。",
            "sections": [],
        }

    client_kwargs = {"api_key": config.anthropic_api_key}
    if config.anthropic_base_url:
        client_kwargs["base_url"] = config.anthropic_base_url

    client = Anthropic(**client_kwargs)
    prompt = _build_prompt(items, config.max_news_per_category)

    response = client.messages.create(
        model=config.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    return _parse_json(content)


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())
