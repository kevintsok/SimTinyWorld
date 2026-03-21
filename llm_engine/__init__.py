"""
LLM引擎初始化模块
提供获取默认LLM引擎的函数
"""

import os
from .factory import LLMEngineFactory
from .base import BaseLLMEngine
from .engine_verifier import EngineVerifier

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
            "model_name": "qwen3.5-flash",
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

# 导出主要类和工厂
__all__ = ['BaseLLMEngine', 'LLMEngineFactory', 'EngineVerifier']

# 便捷函数，从默认引擎类型创建引擎
def create_engine(engine_type=None, **kwargs):
    """
    从默认引擎类型或环境变量指定的引擎类型创建LLM引擎
    
    Args:
        engine_type: 引擎类型，如果为None则使用环境变量DEFAULT_LLM_ENGINE或默认为"qwen"
        **kwargs: 传递给引擎构造函数的参数
        
    Returns:
        BaseLLMEngine: LLM引擎实例
    """
    # 如果未指定引擎类型，从环境变量获取
    if engine_type is None:
        engine_type = os.environ.get("DEFAULT_LLM_ENGINE", "qwen")
    
    return LLMEngineFactory.create_engine(engine_type, **kwargs)

# 便捷函数，验证所有引擎
def verify_engines(display=True):
    """
    验证所有LLM引擎的状态
    
    Args:
        display: 是否显示验证结果
        
    Returns:
        Dict: 引擎状态信息
    """
    verifier = EngineVerifier()
    results = verifier.verify_all_engines()
    
    if display:
        verifier.display_status()
    
    return results

# 检查是否有requirements.txt中的colorama包
def _check_dependencies():
    try:
        import colorama
    except ImportError:
        print("警告: 未安装colorama包，引擎验证器的彩色输出将不可用")
        print("可以通过运行以下命令安装: pip install colorama")

# 导入时检查依赖
_check_dependencies() 