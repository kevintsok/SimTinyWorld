from typing import Optional, Dict, Any
import requests
from .base import BaseLLMEngine
from config.config_manager import ConfigManager

class DeepSeekEngine(BaseLLMEngine):
    """DeepSeek LLM引擎实现"""
    
    def __init__(self, model_name: str = "deepseek-chat", **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_base = kwargs.get("api_base", "https://api.deepseek.com/v1")
        self.embedding_model = kwargs.get("embedding_model", "deepseek-embedding")
        
        # 从配置管理器获取API密钥
        config = ConfigManager.get_instance()
        self.api_key = config.get_api_key("DEEPSEEK")
        if not self.api_key:
            raise ValueError("未找到DeepSeek API密钥")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """使用DeepSeek生成文本"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def get_embeddings(self, text: str) -> list:
        """获取文本嵌入"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.embedding_model,
            "input": text
        }
        
        response = requests.post(
            f"{self.api_base}/embeddings",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"] 