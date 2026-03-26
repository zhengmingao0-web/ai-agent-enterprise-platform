"""
天气查询工具（模拟）
合并 开发者A + 开发者B 的实现
"""
from langchain_core.tools import tool


@tool
def weather_tool(city: str) -> str:
    """
    查询指定城市的实时天气。输入城市名称，返回天气信息。
    示例: "北京", "上海", "深圳"
    """
    # 合并 A 和 B 的城市数据，使用 B 的详细格式
    mock_data = {
        "北京": {"temp": "15°C", "status": "晴",  "humidity": "40%"},
        "上海": {"temp": "18°C", "status": "多云", "humidity": "55%"},
        "广州": {"temp": "22°C", "status": "小雨", "humidity": "80%"},
        "深圳": {"temp": "25°C", "status": "晴",  "humidity": "60%"},
        "成都": {"temp": "16°C", "status": "阴",  "humidity": "75%"},
    }
    data = mock_data.get(city)
    if data:
        return f"{city} | 温度:{data['temp']} 天气:{data['status']} 湿度:{data['humidity']}"
    return f"未找到 {city} 的天气信息"
