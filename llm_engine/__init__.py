"""
LLM引擎初始化模块
提供获取默认LLM引擎的函数
"""

import os
from .factory import LLMEngineFactory

def get_llm_engine(engine_type="qwen"):
    """
    获取默认的LLM引擎实例
    
    Args:
        engine_type: 引擎类型，默认为"qwen"
    
    Returns:
        BaseLLMEngine: LLM引擎实例
    """
    # 获取环境变量中的API密钥
    api_key = os.environ.get("QWEN_API_KEY", "")
    
    # 如果没有设置API密钥，尝试从文件读取
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("QWEN_API_KEY="):
                        api_key = line.strip().split("=")[1].strip()
                        break
        except Exception as e:
            print(f"读取API密钥文件失败: {e}")
    
    # 配置引擎参数
    engine_configs = {
        "qwen": {
            "model_name": "qwen-turbo",
            "api_key": api_key
        },
        "openai": {
            "model_name": "gpt-3.5-turbo",
            "api_key": os.environ.get("OPENAI_API_KEY", "")
        },
        "deepseek": {
            "model_name": "deepseek-chat",
            "api_key": os.environ.get("DEEPSEEK_API_KEY", "")
        }
    }
    
    # 获取指定引擎的配置
    config = engine_configs.get(engine_type, engine_configs["qwen"])
    
    # 创建并返回引擎实例
    return LLMEngineFactory.create_engine(engine_type, **config)

# 导出函数
__all__ = ["get_llm_engine", "LLMEngineFactory"] 