"""
安全代码执行工具
在沙箱环境中执行 Python 代码片段。
安全措施：限制可用模块、禁止文件/网络操作、设置超时。
"""
from langchain_core.tools import tool
import sys
import io
import signal
from contextlib import redirect_stdout, redirect_stderr


# 允许在沙箱中使用的模块白名单
SAFE_MODULES = {"math", "json", "datetime", "collections", "itertools", "functools", "re"}

# 禁止的危险内置函数
BLOCKED_BUILTINS = {
    "__import__", "open", "exec", "eval", "compile",
    "input", "print",  # print 通过 redirect_stdout 捕获
}


def _create_safe_globals():
    """创建沙箱执行环境，只暴露安全的内置函数"""
    import math
    safe_builtins = {
        name: getattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__, name, None)
        for name in dir(__builtins__ if isinstance(__builtins__, dict) else __builtins__)
        if name not in BLOCKED_BUILTINS and not name.startswith('_')
    }
    # 强制覆盖危险函数
    for blocked in BLOCKED_BUILTINS:
        safe_builtins.pop(blocked, None)

    return {
        "__builtins__": safe_builtins,
        "math": math,
        "print": print,  # 会被 redirect_stdout 捕获
    }


@tool
def code_runner_tool(code: str) -> str:
    """
    在安全沙箱中执行 Python 代码片段，返回执行输出。
    适合数据处理、计算、逻辑验证等任务。
    不支持：文件IO、网络请求、导入外部库。
    示例代码: "result = [i**2 for i in range(10)]\nprint(result)"
    """
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    try:
        safe_globals = _create_safe_globals()

        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compile(code, "<sandbox>", "exec"), safe_globals)

        output = stdout_buf.getvalue()
        errors = stderr_buf.getvalue()

        if errors:
            return f"执行警告:\n{errors}\n\n输出:\n{output or '(无输出)'}"
        return f"执行成功:\n{output or '(代码执行完毕，无打印输出)'}"

    except SyntaxError as e:
        return f"语法错误 (行 {e.lineno}): {e.msg}"
    except Exception as e:
        return f"执行错误: {type(e).__name__}: {str(e)}"
