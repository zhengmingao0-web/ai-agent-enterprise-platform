"""
RAG Agent - 检索增强生成
职责：在向量数据库中检索与当前任务相关的文档，
将检索内容作为上下文提供给 DeepSeek，提升回答准确性。
"""
import os
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from backend.config import llm_precise, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from backend.graph.state import AgentState


# ChromaDB 持久化路径
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../chroma_db")

# 使用 DeepSeek 兼容的 embedding（这里用 OpenAI embedding 接口）
# 生产环境可替换为 HuggingFace 本地 embedding 模型节省成本
def _get_vectorstore():
    """懒加载向量数据库，避免启动时就建立连接"""
    try:
        embeddings = OpenAIEmbeddings(
            base_url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY,
            model="text-embedding-ada-002",
        )
        return Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
        )
    except Exception:
        return None


RAG_SYSTEM_PROMPT = """你是一个知识库问答专家。
你将收到从知识库检索到的相关文档片段（上下文），
请基于这些上下文回答问题。
如果上下文不足以回答，请说明并给出合理推断。

上下文：
{context}
"""


def rag_node(state: AgentState) -> dict:
    """
    RAG 节点执行流程：
    1. 读取当前子任务作为查询
    2. 在向量库中检索 Top-K 相关文档
    3. 将文档注入 prompt，调用 DeepSeek 生成回答
    4. 更新任务状态
    """
    plan = state.get("plan", [])
    idx = state.get("current_task_index", 0)

    if idx >= len(plan):
        return {"execution_log": ["[RAGAgent] 无待执行任务"], "next": "router"}

    current_task = plan[idx]
    query = current_task["description"]

    # 尝试从向量库检索
    context_text = ""
    vectorstore = _get_vectorstore()

    if vectorstore:
        try:
            docs = vectorstore.similarity_search(query, k=3)
            if docs:
                context_text = "\n\n---\n\n".join(
                    f"文档[{i+1}]: {doc.page_content}" for i, doc in enumerate(docs)
                )
        except Exception as e:
            context_text = f"(知识库检索失败: {e})"

    if not context_text:
        context_text = "(知识库中未找到相关文档，请基于通用知识回答)"

    messages = [
        SystemMessage(content=RAG_SYSTEM_PROMPT.format(context=context_text)),
        HumanMessage(content=f"问题：{query}")
    ]

    response = llm_precise.invoke(messages)
    result_content = response.content

    # 更新计划状态
    updated_plan = list(plan)
    updated_plan[idx] = {**current_task, "status": "done", "result": result_content}

    tool_results_map = dict(state.get("tool_results", {}))
    tool_results_map[current_task["id"]] = result_content

    log_entry = f"[RAGAgent] 子任务[{idx}] 检索完成，找到上下文 {len(context_text)} 字符"

    return {
        "messages": [AIMessage(content=result_content)],
        "plan": updated_plan,
        "current_task_index": idx + 1,
        "tool_results": tool_results_map,
        "execution_log": [log_entry],
        "next": "router",
    }
