"""
知识搜索工具（演示版）
生产环境中可替换为真实 API：
- Tavily Search（推荐，专为 LLM 设计）
- SerpAPI
- Bing Search API
"""
from langchain_core.tools import tool
from datetime import datetime


# 模拟知识库（生产环境替换为真实 API 调用）
_MOCK_KNOWLEDGE = {
    "deepseek": "DeepSeek 是由深度求索公司开发的大语言模型，支持代码生成、推理、多轮对话，API 兼容 OpenAI 格式。",
    "langgraph": "LangGraph 是 LangChain 团队开发的图状 Agent 框架，支持循环、条件分支、多 Agent 协作。",
    "fastapi": "FastAPI 是基于 Python 的高性能 Web 框架，自动生成 OpenAPI 文档，原生支持异步。",
    "agent": "AI Agent 是能够感知环境、制定计划、执行工具调用的自主AI系统，核心是规划-行动-观察循环。",
    "rag": "RAG (检索增强生成) 通过在生成前检索相关文档，提升LLM回答的准确性和时效性。",
}


@tool
def search_tool(query: str) -> str:
    """
    搜索知识库或互联网获取信息。
    输入查询关键词，返回相关知识内容。
    示例: "DeepSeek 模型特点"
    """
    query_lower = query.lower()

    # 查找匹配的知识条目
    results = []
    for keyword, content in _MOCK_KNOWLEDGE.items():
        if keyword in query_lower or query_lower in content.lower():
            results.append(f"[{keyword}] {content}")

    if results:
        return f"搜索 '{query}' 的结果:\n" + "\n\n".join(results)

    # 无匹配时返回通用回复
    return (
        f"搜索 '{query}' 未找到精确匹配。\n"
        f"建议: 可尝试更具体的关键词，或查询时间: {datetime.now().strftime('%Y-%m-%d')}"
    )
