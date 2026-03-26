"""
工具模块 - 对外暴露所有可用工具
Agent 通过 bind_tools() 绑定这些工具，
DeepSeek 会在需要时自动调用它们（Function Calling）。
"""
from backend.tools.calculator import calculator_tool
from backend.tools.search import search_tool
from backend.tools.code_runner import code_runner_tool

ALL_TOOLS = [calculator_tool, search_tool, code_runner_tool]

__all__ = ["ALL_TOOLS", "calculator_tool", "search_tool", "code_runner_tool"]

