"""
天气查询工具（模拟）
开发者B 新增 - 使用不同实现
"""
from langchain_core.tools import tool


@tool
def weather_tool(city: str) -> str:
    """
    查询指定城市的实时天气。
    示例: "深圳", "成都"
    """
    # B 的实现：返回更详细的格式
    mock_data = {
        "深圳": {"temp": "25°C", "status": "晴", "humidity": "60%"},
        "成都": {"temp": "16°C", "status": "阴", "humidity": "75%"},
        "北京": {"temp": "15°C", "status": "晴", "humidity": "40%"},
    }
    data = mock_data.get(city)
    if data:
        return f"{city} | 温度:{data['temp']} 天气:{data['status']} 湿度:{data['humidity']}"
    return f"未找到 {city} 的天气信息"
