from typing import Optional, Dict, Any
import openai
from .base import BaseLLMEngine
from config.config_manager import ConfigManager

class OpenAIEngine(BaseLLMEngine):
    """OpenAI LLM引擎实现"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(model_name, **kwargs)
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-ada-002")
        
        # 从配置管理器获取API密钥
        config = ConfigManager.get_instance()
        api_key = config.get_api_key("OPENAI")
        if not api_key:
            raise ValueError("未找到OpenAI API密钥")
        
        # 创建OpenAI客户端
        self.client = openai.OpenAI(api_key=api_key, **kwargs)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """使用OpenAI生成文本"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    
    def get_embeddings(self, text: str) -> list:
        """获取文本嵌入"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding 