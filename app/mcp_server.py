"""
MCP 服务定义
提供天气查询的 MCP 工具
"""

from fastmcp import FastMCP

from app.services.weather import get_weather, get_forecast

# 创建 MCP 服务器实例
mcp = FastMCP("weather-server")


@mcp.tool()
async def query_weather(city: str) -> str:
    """
    查询指定城市的实时天气信息
    
    Args:
        city: 城市名称，如"北京"、"上海"、"广州"
        
    Returns:
        格式化的天气信息，包含温度、湿度、风向等
    """
    return await get_weather(city)


@mcp.tool()
async def query_forecast(city: str) -> str:
    """
    查询指定城市的未来天气预报（3天）
    
    Args:
        city: 城市名称，如"北京"、"上海"、"广州"
        
    Returns:
        格式化的天气预报信息
    """
    return await get_forecast(city)
