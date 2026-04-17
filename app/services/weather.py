"""
高德天气服务模块
提供城市编码查询和天气查询功能
"""

import httpx
from typing import Optional, Dict, Any

from app.core.config import get_settings


class WeatherService:
    """天气服务类"""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=10.0)
        # 简单的内存缓存
        self._city_cache: Dict[str, str] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_city_code(self, city_name: str) -> Optional[str]:
        """
        通过城市名获取城市编码（带缓存）
        
        Args:
            city_name: 城市名称，如"北京"、"上海"
            
        Returns:
            城市编码，如"110000"，失败返回None
        """
        # 标准化城市名
        normalized_name = city_name.strip().replace("市", "").replace("省", "")
        
        # 检查缓存
        if normalized_name in self._city_cache:
            return self._city_cache[normalized_name]
        
        # 调用高德地理编码API
        url = f"{self.settings.amap_base_url}/geocode/geo"
        params = {
            "key": self.settings.amap_api_key,
            "address": normalized_name,
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "1" and data.get("geocodes"):
                # 提取城市编码
                adcode = data["geocodes"][0].get("adcode")
                if adcode:
                    # 存入缓存
                    self._city_cache[normalized_name] = adcode
                    return adcode
        except Exception as e:
            print(f"获取城市编码失败: {e}")
        
        return None

    async def get_weather(self, city_name: str) -> Dict[str, Any]:
        """
        获取城市天气信息
        
        Args:
            city_name: 城市名称
            
        Returns:
            天气信息字典
        """
        # 1. 获取城市编码
        city_code = await self.get_city_code(city_name)
        if not city_code:
            return {
                "success": False,
                "error": f"无法识别城市: {city_name}",
                "data": None
            }
        
        # 2. 查询天气
        url = f"{self.settings.amap_base_url}/weather/weatherInfo"
        params = {
            "key": self.settings.amap_api_key,
            "city": city_code,
            "extensions": "base"  # base: 实况天气
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "1" and data.get("lives"):
                weather = data["lives"][0]
                return {
                    "success": True,
                    "city": weather.get("city"),
                    "weather": weather.get("weather"),
                    "temperature": weather.get("temperature"),
                    "humidity": weather.get("humidity"),
                    "winddirection": weather.get("winddirection"),
                    "windpower": weather.get("windpower"),
                    "reporttime": weather.get("reporttime"),
                    "data": weather
                }
            else:
                return {
                    "success": False,
                    "error": "获取天气数据失败",
                    "data": data
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"请求异常: {str(e)}",
                "data": None
            }

    async def get_weather_forecast(self, city_name: str) -> Dict[str, Any]:
        """
        获取城市天气预报（未来3天）
        
        Args:
            city_name: 城市名称
            
        Returns:
            天气预报字典
        """
        # 1. 获取城市编码
        city_code = await self.get_city_code(city_name)
        if not city_code:
            return {
                "success": False,
                "error": f"无法识别城市: {city_name}",
                "data": None
            }
        
        # 2. 查询预报天气
        url = f"{self.settings.amap_base_url}/weather/weatherInfo"
        params = {
            "key": self.settings.amap_api_key,
            "city": city_code,
            "extensions": "all"  # all: 预报天气
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "1" and data.get("forecasts"):
                forecast = data["forecasts"][0]
                casts = forecast.get("casts", [])
                return {
                    "success": True,
                    "city": forecast.get("city"),
                    "reporttime": forecast.get("reporttime"),
                    "forecasts": casts,
                    "data": forecast
                }
            else:
                return {
                    "success": False,
                    "error": "获取天气预报失败",
                    "data": data
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"请求异常: {str(e)}",
                "data": None
            }


# 便捷函数
async def get_weather(city: str) -> str:
    """
    获取天气的便捷函数，返回格式化字符串
    
    Args:
        city: 城市名称
        
    Returns:
        格式化的天气信息字符串
    """
    async with WeatherService() as service:
        result = await service.get_weather(city)
        
        if result["success"]:
            return (
                f"【{result['city']}天气】\n"
                f"天气状况：{result['weather']}\n"
                f"温度：{result['temperature']}℃\n"
                f"湿度：{result['humidity']}%\n"
                f"风向：{result['winddirection']}\n"
                f"风力：{result['windpower']}\n"
                f"发布时间：{result['reporttime']}"
            )
        else:
            return f"查询失败：{result['error']}"


async def get_forecast(city: str) -> str:
    """
    获取天气预报的便捷函数，返回格式化字符串
    
    Args:
        city: 城市名称
        
    Returns:
        格式化的天气预报字符串
    """
    async with WeatherService() as service:
        result = await service.get_weather_forecast(city)
        
        if result["success"]:
            lines = [f"【{result['city']}未来天气预报】\n"]
            for day in result["forecasts"][:3]:
                lines.append(
                    f"{day.get('date')}："
                    f"{day.get('dayweather')}，"
                    f"{day.get('daytemp')}℃/"
                    f"{day.get('nighttemp')}℃"
                )
            return "\n".join(lines)
        else:
            return f"查询失败：{result['error']}"
