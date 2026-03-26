"""
天气查询工具（模拟）
开发者A 新增
"""
from langchain_core.tools import tool


@tool
def weather_tool(city: str) -> str:
    """
    查询指定城市的天气。输入城市名称，返回天气信息。
    示例: "北京", "上海"
    """
    # 模拟数据
    mock_data = {
        "北京": "晴，15°C，东风3级",
        "上海": "多云，18°C，南风2级",
        "广州": "小雨，22°C，北风1级",
    }
    result = mock_data.get(city, f"暂无 {city} 的天气数据")
    return f"{city} 天气：{result}"
