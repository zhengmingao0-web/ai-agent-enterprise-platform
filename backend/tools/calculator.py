"""
计算器工具
使用 @tool 装饰器，LangChain 自动生成工具的 JSON Schema，
DeepSeek 通过 Function Calling 知道何时、如何调用它。
"""
from langchain_core.tools import tool
import ast
import operator as op


# 允许的数学运算符（防止代码注入）
ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def _safe_eval(node):
    """递归解析 AST 节点，只允许数学表达式，拒绝任意代码执行"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise ValueError(f"不支持的运算符: {op_type}")
        return ALLOWED_OPERATORS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise ValueError(f"不支持的一元运算符: {op_type}")
        return ALLOWED_OPERATORS[op_type](_safe_eval(node.operand))
    else:
        raise ValueError(f"不支持的表达式类型: {type(node)}")


@tool
def calculator_tool(expression: str) -> str:
    """
    安全数学计算器。输入数学表达式字符串，返回计算结果。
    支持: +, -, *, /, ** (幂运算)
    示例: "2 ** 10 + 100 / 4"
    """
    try:
        tree = ast.parse(expression, mode='eval')
        result = _safe_eval(tree.body)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算失败: {str(e)}"
