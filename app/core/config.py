"""
应用配置模块
使用 Pydantic Settings 管理环境变量
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用信息
    app_name: str = "Weather MCP Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 高德地图API
    amap_api_key: str = ""  # 从环境变量读取，必填
    amap_base_url: str = "https://restapi.amap.com/v3"

    # CORS配置
    allowed_origins: str = "*"

    # 日志配置
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> List[str]:
        """解析CORS允许的域名列表"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
