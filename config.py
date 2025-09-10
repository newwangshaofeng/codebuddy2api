"""
Configuration management for CodeBuddy2API
"""
import os
from typing import Optional

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有 python-dotenv，手动解析 .env 文件
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def get_server_host() -> str:
    """获取服务器主机地址"""
    return os.getenv("CODEBUDDY_HOST", "127.0.0.1")


def get_server_port() -> int:
    """获取服务器端口"""
    return int(os.getenv("CODEBUDDY_PORT", "8001"))


def get_server_password() -> Optional[str]:
    """获取服务器密码"""
    return os.getenv("CODEBUDDY_PASSWORD")


def get_codebuddy_api_endpoint() -> str:
    """获取CodeBuddy API端点"""
    return os.getenv("CODEBUDDY_API_ENDPOINT", "https://www.codebuddy.ai")


def get_codebuddy_creds_dir() -> str:
    """获取凭证文件目录"""
    return os.getenv("CODEBUDDY_CREDS_DIR", ".codebuddy_creds")


def get_log_level() -> str:
    """获取日志级别"""
    return os.getenv("CODEBUDDY_LOG_LEVEL", "INFO")


def get_available_models() -> list:
    """获取可用模型列表"""
    models_str = os.getenv("CODEBUDDY_MODELS", "claude-4.0,claude-3.7,gpt-5,gpt-5-mini,gpt-5-nano,o4-mini,gemini-2.5-flash,gemini-2.5-pro,auto-chat")
    return [model.strip() for model in models_str.split(",")]

