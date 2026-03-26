"""
Router Agent - 智能任务路由器
职责：根据当前任务计划，决定下一步交给哪个 Agent 执行。

设计原则：路由逻辑基于 Planner 生成的计划，
不依赖 LLM 判断，确保 100% 确定性、零延迟、零幻觉。
"""
from langchain_core.messages import AIMessage
from backend.graph.state import AgentState

# 支持的 Agent 路由目标
VALID_AGENTS = {"tool_agent", "rag_agent", "report_agent"}


def router_node(state: AgentState) -> dict:
    """
    路由节点逻辑：
    1. 检查是否还有待执行的子任务
    2. 找到当前待执行任务，读取其指定的 agent
    3. 设置 next 字段，LangGraph 根据此字段决定下一个节点
    """
    plan = state.get("plan", [])
    idx = state.get("current_task_index", 0)

    # 边界检查：计划为空或已全部完成
    if not plan or idx >= len(plan):
        return {
            "messages": [AIMessage(content="所有任务已完成，准备结束。")],
            "execution_log": ["[Router] 所有子任务已完成 → 结束"],
            "next": "finish",
        }

    current_task = plan[idx]
    target_agent = current_task["agent"]

    # 校验目标 Agent 是否存在
    if target_agent not in VALID_AGENTS:
        target_agent = "tool_agent"  # 降级兜底

    log_entry = f"[Router] 子任务[{idx}] '{current_task['description']}' → {target_agent}"

    return {
        "execution_log": [log_entry],
        "next": target_agent,
    }
