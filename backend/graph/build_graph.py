"""
LangGraph 任务流图构建
将所有 Agent 节点连接成有向图，实现多 Agent 协作。

图结构：
    [START]
      ↓
   planner (分解任务)
      ↓
   router (读取计划，决定路由)
      ↓
  ┌────┬────────┬─────────────┐
  ↓    ↓        ↓             ↓
tool  rag   report_agent   [END]
agent agent     ↓
  ↓    ↓    [END]
  └────┘
    ↓
  router (继续下一个子任务)
"""
from langgraph.graph import StateGraph, END
from backend.graph.state import AgentState
from backend.agents.planner import planner_node
from backend.agents.router import router_node
from backend.agents.tool_agent import tool_agent_node
from backend.agents.rag_agent import rag_node
from backend.agents.report_agent import report_agent_node


def build_graph():
    """
    构建并编译多 Agent 任务图。

    关键设计：
    - router 是中心枢纽，每个专业 Agent 执行完后都回到 router
    - router 根据 plan[current_task_index].agent 决定下一步
    - add_conditional_edges 实现动态路由（不同于普通的固定边）
    - 当所有任务完成，router 返回 'finish'，流程结束
    """
    graph = StateGraph(AgentState)

    # ── 注册所有节点 ────────────────────────────────────────────
    graph.add_node("planner", planner_node)
    graph.add_node("router", router_node)
    graph.add_node("tool_agent", tool_agent_node)
    graph.add_node("rag_agent", rag_node)
    graph.add_node("report_agent", report_agent_node)

    # ── 固定边：入口 → planner → router ────────────────────────
    graph.set_entry_point("planner")
    graph.add_edge("planner", "router")

    # ── 条件边：router 根据 state["next"] 动态路由 ────────────
    graph.add_conditional_edges(
        "router",
        lambda state: state["next"],
        {
            "tool_agent": "tool_agent",
            "rag_agent": "rag_agent",
            "report_agent": "report_agent",
            "finish": END,
        }
    )

    # ── 回环边：专业 Agent 执行完后回到 router ─────────────────
    # 这形成了"执行循环"，每次循环处理一个子任务
    graph.add_edge("tool_agent", "router")
    graph.add_edge("rag_agent", "router")

    # report_agent 是终止节点，直接结束
    graph.add_conditional_edges(
        "report_agent",
        lambda state: "finish",
        {"finish": END}
    )

    return graph.compile()
