"""
Planner Agent - 任务规划器
职责：分析用户意图，将复杂任务拆解为有序子任务列表，
并为每个子任务指定负责的 Agent。
"""
import json
import uuid
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.config import llm_precise
from backend.graph.state import AgentState, SubTask


PLANNER_SYSTEM_PROMPT = """你是一个企业级任务规划专家。
你的职责是将用户的复杂请求分解为清晰、可执行的子任务序列。

可用的执行 Agent：
- tool_agent: 调用工具（搜索、计算、代码执行）
- rag_agent: 检索知识库中的相关文档
- report_agent: 汇总结果，生成结构化报告

规则：
1. 分解为 2-5 个子任务，每个子任务职责单一
2. 最后一个子任务必须分配给 report_agent
3. 严格只返回 JSON，不要任何额外说明

返回格式：
{
  "tasks": [
    {"description": "子任务描述", "agent": "agent名称"},
    ...
  ]
}
"""


def planner_node(state: AgentState) -> dict:
    """
    Planner 节点：
    1. 读取用户输入
    2. 调用 DeepSeek 生成任务计划
    3. 解析 JSON 并构建 SubTask 列表
    4. 返回更新后的状态
    """
    user_input = state["user_input"]

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"用户请求：{user_input}")
    ]

    response = llm_precise.invoke(messages)
    raw_content = response.content.strip()

    # 处理 DeepSeek 可能返回的 markdown 代码块
    if raw_content.startswith("```"):
        lines = raw_content.split("\n")
        raw_content = "\n".join(lines[1:-1])

    try:
        plan_data = json.loads(raw_content)
        tasks_raw = plan_data.get("tasks", [])
    except json.JSONDecodeError:
        # 解析失败时使用保底计划
        tasks_raw = [
            {"description": f"处理用户请求: {user_input}", "agent": "tool_agent"},
            {"description": "生成任务执行报告", "agent": "report_agent"},
        ]

    # 构建结构化子任务列表
    plan: list[SubTask] = [
        SubTask(
            id=f"task_{i}",
            description=task["description"],
            agent=task.get("agent", "tool_agent"),
            status="pending",
            result=None,
        )
        for i, task in enumerate(tasks_raw)
    ]

    log_entry = f"[Planner] 已生成 {len(plan)} 个子任务计划"

    return {
        "messages": [AIMessage(content=f"任务计划已生成：{json.dumps([t['description'] for t in plan], ensure_ascii=False)}")],
        "plan": plan,
        "current_task_index": 0,
        "tool_results": {},
        "execution_log": [log_entry],
        "next": "router",
    }
