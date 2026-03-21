import os
from typing import Optional, Dict, Any, Type, List
from .base import BaseLLMEngine

# 全局引擎单例
_global_engine: Optional[Any] = None
_global_engine_type: Optional[str] = None

# 懒加载引擎类
_engine_classes: Dict[str, Any] = {}


def _get_engine_class(engine_type: str):
    """懒加载引擎类"""
    if engine_type not in _engine_classes:
        if engine_type == "qwen":
            from .qwen import QwenEngine
            _engine_classes[engine_type] = QwenEngine
        elif engine_type == "openai":
            from .openai import OpenAIEngine
            _engine_classes[engine_type] = OpenAIEngine
        elif engine_type == "deepseek":
            from .deepseek import DeepSeekEngine
            _engine_classes[engine_type] = DeepSeekEngine
        else:
            raise ValueError(f"不支持的引擎类型: {engine_type}")
    return _engine_classes[engine_type]


class LLMEngineFactory:
    """LLM引擎工厂类，负责创建不同类型的LLM引擎实例"""

    _engines = {}  # 懒加载
    
    @classmethod
    def create_engine(cls, engine_type: str, **kwargs):
        """
        创建LLM引擎实例

        Args:
            engine_type: 引擎类型，可选值：qwen, openai, deepseek
            **kwargs: 引擎初始化参数，可以包括：
                - model_name: 模型名称，如gpt-3.5-turbo, qwen-plus等
                - temperature: 温度参数，控制输出的随机性
                - top_p: 控制输出多样性的参数
                - max_tokens: 最大生成令牌数
                - api_key: API密钥，如果不提供则从环境变量或配置管理器获取
                - mock_mode: 是否使用模拟模式，默认False

        Returns:
            LLM引擎实例

        Raises:
            ValueError: 如果指定的引擎类型不存在
        """
        engine_class = _get_engine_class(engine_type.lower())
        return engine_class(**kwargs)
    
    @classmethod
    def register_engine(cls, name: str, engine_class: Type[BaseLLMEngine]):
        """
        注册新的LLM引擎
        
        Args:
            name: 引擎名称
            engine_class: 引擎类，必须是BaseLLMEngine的子类
        
        Raises:
            TypeError: 如果engine_class不是BaseLLMEngine的子类
        """
        if not issubclass(engine_class, BaseLLMEngine):
            raise TypeError(f"引擎类必须是BaseLLMEngine的子类")
            
        cls._engines[name.lower()] = engine_class
        
    @classmethod
    def get_available_engines(cls) -> Dict[str, str]:
        """
        获取所有可用的引擎类型

        Returns:
            Dict[str, str]: 引擎名称映射
        """
        # 返回已知引擎类型，不触发导入
        return {"qwen": "qwen", "openai": "openai", "deepseek": "deepseek"}
        
    @classmethod
    def verify_engines(cls, check_actual_api: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        验证所有LLM引擎的状态
        
        Args:
            check_actual_api: 是否执行实际的API调用来验证引擎状态，默认为True
            
        Returns:
            Dict[str, Dict[str, Any]]: 每个引擎的状态信息，包括：
                - available: 是否可用
                - mock_mode: 是否处于模拟模式 
                - error: 如果有错误，错误信息
                - models: 可用的模型列表（如果可以获取到）
        """
        results = {}
        
        try:
            for engine_name, engine_class in cls._engines.items():
                engine_status = {
                    "available": False,
                    "mock_mode": True,
                    "error": None,
                    "models": []
                }
                
                try:
                    # 尝试初始化引擎
                    engine_instance = engine_class()
                    
                    # 检查是否处于模拟模式
                    engine_status["mock_mode"] = engine_instance.mock_mode
                    
                    # 如果不是模拟模式，则认为可用
                    if not engine_instance.mock_mode:
                        engine_status["available"] = True
                        
                        # 如果需要进一步验证API，执行简单的API调用
                        if check_actual_api:
                            try:
                                # 执行一个简单的生成请求
                                response = engine_instance.generate("Hello", max_tokens=5)
                                if response:
                                    engine_status["available"] = True
                                else:
                                    engine_status["available"] = False
                                    engine_status["error"] = "API返回空响应"
                            except Exception as e:
                                engine_status["available"] = False
                                engine_status["error"] = f"API调用失败: {str(e)}"
                        
                        # 尝试从配置中获取支持的模型列表
                        try:
                            from llm_engine.config.config_manager import ConfigManager
                            config = ConfigManager.get_instance()
                            models_config = config.models_config.get(engine_name, {}).get("models", {})
                            if models_config and isinstance(models_config, dict):
                                engine_status["models"] = list(models_config.keys())
                        except Exception as e:
                            print(f"获取模型列表失败: {e}")
                    
                except Exception as e:
                    engine_status["available"] = False
                    engine_status["error"] = str(e)
                
                results[engine_name] = engine_status
        except Exception as e:
            print(f"验证引擎时出错: {e}")
            # 确保始终返回结果，即使出现错误
            if not results:
                for engine_name in cls._engines.keys():
                    results[engine_name] = {
                        "available": False,
                        "mock_mode": True,
                        "error": f"验证过程出错: {str(e)}",
                        "models": []
                    }
            
        return results


def get_global_engine(engine_type: str = None, **kwargs) -> BaseLLMEngine:
    """
    获取全局引擎单例（懒加载）

    首次调用时创建引擎实例，之后返回同一实例。

    Args:
        engine_type: 引擎类型，如果为None则从环境变量 DEFAULT_LLM_ENGINE 获取
        **kwargs: 引擎初始化参数

    Returns:
        BaseLLMEngine: LLM引擎实例
    """
    global _global_engine, _global_engine_type

    # 如果已存在且引擎类型相同，直接返回
    if _global_engine is not None and _global_engine_type == engine_type:
        return _global_engine

    # 确定引擎类型
    if engine_type is None:
        engine_type = os.environ.get("DEFAULT_LLM_ENGINE", "qwen")

    # 创建引擎实例
    _global_engine = LLMEngineFactory.create_engine(engine_type, **kwargs)
    _global_engine_type = engine_type

    return _global_engine


def set_global_engine(engine: BaseLLMEngine, engine_type: str = None):
    """
    设置全局引擎单例

    Args:
        engine: LLM引擎实例
        engine_type: 引擎类型名称
    """
    global _global_engine, _global_engine_type
    _global_engine = engine
    _global_engine_type = engine_type or engine.__class__.__name__.lower().replace("engine", "")


def has_global_engine() -> bool:
    """检查是否已存在全局引擎"""
    return _global_engine is not None 