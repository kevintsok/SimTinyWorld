from typing import Optional, Dict, Any
from .base import BaseLLMEngine
from .qwen import QwenEngine
from .openai import OpenAIEngine
from .deepseek import DeepSeekEngine

class LLMEngineFactory:
    """LLM引擎工厂类"""
    
    _engines = {
        "qwen": QwenEngine,
        "openai": OpenAIEngine,
        "deepseek": DeepSeekEngine
    }
    
    @classmethod
    def create_engine(cls, engine_type: str, **kwargs) -> BaseLLMEngine:
        """
        创建LLM引擎实例
        
        Args:
            engine_type: 引擎类型，可选值：qwen, openai, deepseek
            **kwargs: 引擎初始化参数
        
        Returns:
            BaseLLMEngine: LLM引擎实例
        
        Raises:
            ValueError: 如果指定的引擎类型不存在
        """
        engine_class = cls._engines.get(engine_type.lower())
        if not engine_class:
            raise ValueError(f"不支持的引擎类型: {engine_type}")
        
        return engine_class(**kwargs)
    
    @classmethod
    def register_engine(cls, name: str, engine_class: type):
        """
        注册新的LLM引擎
        
        Args:
            name: 引擎名称
            engine_class: 引擎类
        """
        cls._engines[name.lower()] = engine_class 