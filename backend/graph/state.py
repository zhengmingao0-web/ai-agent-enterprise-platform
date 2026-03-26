"""
企业级 Agent 状态定义
LangGraph 的每个节点读取并更新这个共享状态，
类似一个"任务执行白板"，所有Agent都写在上面。
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class SubTask(TypedDict):
    """单个子任务的结构"""
    id: str                   # 子任务唯一ID，如 "task_1"
    description: str          # 子任务描述
    agent: str                # 负责执行的 Agent 名称
    status: str               # pending | running | done | failed
    result: Optional[str]     # 执行结果


class AgentState(TypedDict):
    """
    全局 Agent 执行状态

    Annotated[list, operator.add] 表示这个字段是"累加"的：
    每个节点只需返回新增的消息，LangGraph 自动拼接，
    避免每次都传完整列表造成的数据冗余。
    """
    # 对话消息历史（累加模式）
    messages: Annotated[List[BaseMessage], operator.add]

    # 路由控制：下一步去哪个 Agent
    next: str

    # 原始用户输入，方便各 Agent 随时访问
    user_input: str

    # Planner 生成的子任务列表
    plan: List[SubTask]

    # 当前正在执行的子任务索引
    current_task_index: int

    # 各 Agent 的工具调用结果（键=子任务ID）
    tool_results: Dict[str, Any]

    # 执行轨迹日志（用于前端实时展示）
    execution_log: Annotated[List[str], operator.add]

    # 最终生成的报告
    final_report: Optional[str]

    # 错误信息
    error: Optional[str]
