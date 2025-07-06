"""
项目配置模块

使用 pydantic-settings 管理所有配置项，支持从环境变量读取配置。
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv
import os

# Construct the absolute path to the .env file to avoid any ambiguity
# The root is the '02backend' directory. __file__ is in '.../src/core/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Use the exact filename, including the leading space
ENV_FILE_PATH = PROJECT_ROOT / ". env"

# Explicitly load the .env file from the constructed absolute path.
print(f">>> [DEBUG] Attempting to load env file from: {ENV_FILE_PATH}")
if ENV_FILE_PATH.exists():
    load_dotenv(ENV_FILE_PATH)
    print(">>> [DEBUG] Env file found and loaded by python-dotenv.")
else:
    print(">>> [DEBUG] Env file NOT FOUND at the specified path.")


class Settings(BaseSettings):
    """项目配置类"""
    
    model_config = SettingsConfigDict(
        # Pass the absolute path to pydantic-settings as well
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # 项目基础配置
    app_name: str = "Deniom API"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API 配置
    api_v1_prefix: str = "/api/v1"
    
    # 数据库配置
    database_url: str = "sqlite:///./deniom.db"
    
    # Gemini API 配置
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-pro"
    gemini_project_id: Optional[str] = None  # Vertex AI 项目ID
    
    # 网络配置 - 修复代理配置读取
    http_proxy: Optional[str] = None  # 例如: "http://127.0.0.1:7890"
    https_proxy: Optional[str] = None  # 例如: "http://127.0.0.1:7890"
    request_timeout: int = 60  # 请求超时时间（秒）
    
    # GitHub API 配置
    github_token: Optional[str] = None
    
    # 网络搜索 API 配置 (Serper)
    serper_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None  # SerpApi配置
    
    # 路径配置
    base_dir: Path = PROJECT_ROOT
    data_dir: Path = base_dir / "data"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        
        # 手动从环境变量读取代理配置（解决pydantic-settings读取问题）
        if not self.http_proxy:
            self.http_proxy = os.getenv('HTTP_PROXY')
        if not self.https_proxy:
            self.https_proxy = os.getenv('HTTPS_PROXY')


# 创建全局配置实例
settings = Settings() 