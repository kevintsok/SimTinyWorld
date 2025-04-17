from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseLLMEngine(ABC):
    """LLM引擎基类"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本的抽象方法"""
        pass
    
    @abstractmethod
    def get_embeddings(self, text: str) -> list:
        """获取文本嵌入的抽象方法"""
        pass 