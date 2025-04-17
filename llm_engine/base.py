from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, List
import json
import os

class BaseLLMEngine(ABC):
    """LLM引擎基类，提供通用接口"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        self.mock_mode = kwargs.get("mock_mode", False)
        
        # 加载模型配置
        self.models_config = self._load_models_config()
        
        # 获取当前模型的配置
        self.model_config = self._get_model_config(model_name)
        
        # 设置默认参数
        self.temperature = kwargs.get("temperature", self.model_config.get("temperature", 0.7))
        self.top_p = kwargs.get("top_p", self.model_config.get("top_p", 0.9))
        self.max_tokens = kwargs.get("max_tokens", self.model_config.get("max_tokens", 4096))
    
    def _load_models_config(self) -> Dict:
        """加载模型配置文件"""
        config_path = os.path.join("llm_engine", "config", "models_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"警告: 模型配置文件 {config_path} 不存在，使用默认配置")
                return {}
        except Exception as e:
            print(f"加载模型配置文件出错: {e}")
            return {}
    
    def _get_model_config(self, model_name: str) -> Dict:
        """获取指定模型的配置"""
        # 获取LLM提供商类型（例如qwen、openai等）
        provider_type = self.__class__.__name__.lower().replace("engine", "")
        
        # 查找该提供商下的模型配置
        provider_config = self.models_config.get(provider_type, {})
        models = provider_config.get("models", {})
        
        # 返回模型配置，如果没有找到则返回空字典
        return models.get(model_name, {})
    
    @abstractmethod
    def generate(self, prompt: str, think: bool = False, **kwargs) -> str:
        """
        生成文本的抽象方法
        
        Args:
            prompt: 输入提示
            think: 是否使用思考模式
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        pass
    
    @abstractmethod
    def get_embeddings(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        获取文本嵌入的抽象方法
        
        Args:
            texts: 输入文本或文本列表
            
        Returns:
            Union[List[float], List[List[float]]]: 嵌入向量或向量列表
        """
        pass
    
    def _get_system_prompt(self, think: bool = False) -> str:
        """
        根据是否使用思考模式返回系统提示
        
        Args:
            think: 是否使用思考模式
            
        Returns:
            str: 系统提示
        """
        if think:
            return (
                "请深入思考以下问题或任务，分析各个方面，考虑不同的角度和可能性。"
                "首先阐述关键概念和原理，然后逐步分析，最后给出全面而深入的回答。"
                "当涉及复杂问题时，请展示你的推理过程，包括考虑的假设、限制和权衡。"
            )
        else:
            return "你是一个有用的助手。" 