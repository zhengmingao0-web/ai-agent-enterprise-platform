"""
Report Agent - 最终报告生成器
职责：汇总所有子任务执行结果，生成结构化的专业报告。
这是任务流水线的最后一个节点。
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.config import llm_creative
from backend.graph.state import AgentState


REPORT_SYSTEM_PROMPT = """你是一个专业报告撰写专家。
请将以下任务执行结果整合为一份清晰、结构化的报告。

报告格式要求：
1. **执行摘要** - 用2-3句话概括任务结果
2. **详细结果** - 按子任务分段展示
3. **关键发现** - 提炼3-5条核心洞察
4. **建议行动** - 给出后续行动建议

使用 Markdown 格式，确保报告专业、易读。
"""


def report_agent_node(state: AgentState) -> dict:
    """
    报告节点执行流程：
    1. 收集所有子任务的执行结果
    2. 调用 DeepSeek（高温度，更流畅）生成报告
    3. 将报告存入 final_report 字段
    4. 设置 next = finish，结束整个流程
    """
    plan = state.get("plan", [])
    tool_results = state.get("tool_results", {})
    user_input = state["user_input"]

    # 构建子任务结果摘要
    tasks_summary = []
    for task in plan:
        if task["status"] in ("done",) and task.get("result"):
            tasks_summary.append(
                f"子任务: {task['description']}\n结果: {task['result']}"
            )

    tasks_text = "\n\n".join(tasks_summary) if tasks_summary else "（子任务执行中）"

    messages = [
        SystemMessage(content=REPORT_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"原始用户需求：{user_input}\n\n"
            f"各子任务执行结果：\n{tasks_text}"
        ))
    ]

    response = llm_creative.invoke(messages)
    report_content = response.content

    log_entry = f"[ReportAgent] 报告生成完毕，共 {len(report_content)} 字"

    return {
        "messages": [AIMessage(content=report_content)],
        "final_report": report_content,
        "execution_log": [log_entry],
        "next": "finish",
    }
