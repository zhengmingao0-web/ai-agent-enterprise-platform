"""
翻译工具（模拟）
开发者B 新增
"""
from langchain_core.tools import tool


@tool
def translation_tool(text: str, target_lang: str = "英文") -> str:
    """
    将文本翻译成目标语言（模拟）。
    参数: text=要翻译的文字, target_lang=目标语言（英文/日文/法文）
    示例: text="你好", target_lang="英文"
    """
    mock = {
        "英文": {"你好": "Hello", "谢谢": "Thank you", "再见": "Goodbye"},
        "日文": {"你好": "こんにちは", "谢谢": "ありがとう", "再见": "さようなら"},
        "法文": {"你好": "Bonjour", "谢谢": "Merci", "再见": "Au revoir"},
    }
    result = mock.get(target_lang, {}).get(text)
    if result:
        return f"{text} → {result}（{target_lang}）"
    return f"暂不支持翻译: {text} → {target_lang}"
