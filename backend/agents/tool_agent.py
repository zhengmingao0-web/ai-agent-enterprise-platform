"""
Tool Agent - 工具调用执行器
实现 ReAct 模式：Reasoning(推理) + Acting(行动)
DeepSeek 通过 Function Calling 自主决定调用哪个工具，
ToolNode 负责实际执行工具并返回结果。
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from backend.config import llm_precise
from backend.tools import ALL_TOOLS
from backend.graph.state import AgentState


# 将工具绑定到 LLM，DeepSeek 会在需要时通过 Function Calling 触发
llm_with_tools = llm_precise.bind_tools(ALL_TOOLS)

# LangGraph 内置节点，自动解析 AI 返回的 tool_calls 并执行对应工具
tool_executor = ToolNode(ALL_TOOLS)

TOOL_AGENT_PROMPT = """你是一个专业的任务执行助手。
你有以下工具可以使用：
- calculator_tool: 数学计算
- search_tool: 知识搜索
- code_runner_tool: Python 代码执行

请根据当前子任务，选择合适的工具完成任务。
如果不需要工具，直接给出分析结果。
"""


def tool_agent_node(state: AgentState) -> dict:
    """
    Tool Agent 执行流程：
    1. 读取当前子任务描述
    2. 调用 DeepSeek（附带工具列表）
    3. 如果 DeepSeek 请求工具调用，执行工具
    4. 将结果存入 tool_results，更新任务状态
    """
    plan = state.get("plan", [])
    idx = state.get("current_task_index", 0)

    if idx >= len(plan):
        return {"execution_log": ["[ToolAgent] 无待执行任务"], "next": "router"}

    current_task = plan[idx]
    user_input = state["user_input"]

    # 构建上下文提示
    messages = [
        SystemMessage(content=TOOL_AGENT_PROMPT),
        HumanMessage(content=(
            f"原始用户需求：{user_input}\n\n"
            f"当前子任务：{current_task['description']}"
        ))
    ]

    # 第一次调用：LLM 决定是否要调用工具
    ai_response = llm_with_tools.invoke(messages)
    messages.append(ai_response)

    # 如果 LLM 发出了工具调用请求（tool_calls 不为空）
    if ai_response.tool_calls:
        # ToolNode 自动执行所有工具调用，返回 ToolMessage 列表
        tool_results = tool_executor.invoke({"messages": messages})
        tool_messages = tool_results["messages"]
        messages.extend(tool_messages)

        # 二次调用：LLM 根据工具结果生成最终回答
        final_response = llm_with_tools.invoke(messages)
        result_content = final_response.content
    else:
        # 不需要工具，直接使用 LLM 的回答
        result_content = ai_response.content

    # 更新计划：标记当前任务完成
    updated_plan = list(plan)
    updated_plan[idx] = {**current_task, "status": "done", "result": result_content}

    # 存储工具执行结果
    tool_results_map = dict(state.get("tool_results", {}))
    tool_results_map[current_task["id"]] = result_content

    log_entry = f"[ToolAgent] 子任务[{idx}] '{current_task['description']}' 完成"

    return {
        "messages": [AIMessage(content=result_content)],
        "plan": updated_plan,
        "current_task_index": idx + 1,
        "tool_results": tool_results_map,
        "execution_log": [log_entry],
        "next": "router",
    }
