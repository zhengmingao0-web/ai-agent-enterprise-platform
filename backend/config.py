"""
全局配置中心
- DeepSeek LLM 客户端懒加载（延迟到首次使用时初始化，确保 .env 已加载）
- 可在此切换模型、温度参数
"""
import os
from functools import lru_cache
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# config.py 自己加载一次，确保任何导入顺序下都能读到环境变量
load_dotenv()

# ── DeepSeek API 配置 ──────────────────────────────────────────
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")


def _get_api_key() -> str:
    """每次从环境变量读取，确保 load_dotenv() 之后可用"""
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY 未设置，请在 .env 文件中配置")
    return key


@lru_cache(maxsize=8)
def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """
    返回 DeepSeek LLM 实例（懒加载单例）。
    相同 temperature 只创建一次，lru_cache 保证复用。
    """
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        base_url=DEEPSEEK_BASE_URL,
        api_key=_get_api_key(),
        temperature=temperature,
        streaming=True,
    )


# ── 预定义常用 LLM 配置（属性访问，懒加载）──────────────────
# 使用函数而非模块级变量，避免导入时就创建实例

def get_precise_llm() -> ChatOpenAI:
    """精确模式：用于路由/规划，temperature=0"""
    return get_llm(0.0)


def get_creative_llm() -> ChatOpenAI:
    """创意模式：用于报告/总结，temperature=0.7"""
    return get_llm(0.7)


# 兼容旧代码的别名（懒属性）
class _LLMProxy:
    """代理对象，首次访问时才初始化 LLM"""
    def __init__(self, temp):
        self._temp = temp
        self._instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_llm(self._temp)
        return getattr(self._instance, name)

    def invoke(self, *args, **kwargs):
        return get_llm(self._temp).invoke(*args, **kwargs)

    def bind_tools(self, *args, **kwargs):
        return get_llm(self._temp).bind_tools(*args, **kwargs)

    def stream(self, *args, **kwargs):
        return get_llm(self._temp).stream(*args, **kwargs)


llm_precise = _LLMProxy(0.0)
llm_creative = _LLMProxy(0.7)
