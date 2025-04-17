import os
import json
import logging
from typing import Dict, Any, Optional, ClassVar

class ConfigManager:
    """配置管理器，负责管理API密钥和配置信息"""
    
    _instance: ClassVar[Optional['ConfigManager']] = None
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = "llm_engine/config"
        self.api_keys_file = os.path.join(self.config_dir, "api_keys.json")
        self.models_config_file = os.path.join(self.config_dir, "models_config.json")
        
        # 加载API密钥
        self.api_keys = self._load_api_keys()
        
        # 加载模型配置
        self.models_config = self._load_models_config()
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """获取ConfigManager的单例实例
        
        Returns:
            ConfigManager: ConfigManager的单例实例
        """
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
    
    def _load_api_keys(self) -> Dict[str, str]:
        """加载API密钥
        
        Returns:
            Dict[str, str]: API密钥字典 {提供商: 密钥}
        """
        if os.path.exists(self.api_keys_file):
            try:
                with open(self.api_keys_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"加载API密钥文件出错: {e}")
        return {}
    
    def _load_models_config(self) -> Dict[str, Any]:
        """加载模型配置
        
        Returns:
            Dict[str, Any]: 模型配置字典
        """
        if os.path.exists(self.models_config_file):
            try:
                with open(self.models_config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"加载模型配置文件出错: {e}")
        return {}
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """获取指定提供商的API密钥
        
        Args:
            provider: 提供商名称，如OPENAI, QWEN, DEEPSEEK
            
        Returns:
            Optional[str]: API密钥，如果不存在则返回None
        """
        # 先尝试从环境变量获取
        env_var = f"{provider.upper()}_API_KEY"
        if os.environ.get(env_var):
            return os.environ.get(env_var)
            
        # 再从配置文件获取
        return self.api_keys.get(provider.upper())
    
    def set_api_key(self, provider: str, api_key: str) -> None:
        """设置API密钥
        
        Args:
            provider: 提供商名称，如OPENAI, QWEN, DEEPSEEK
            api_key: API密钥
        """
        self.api_keys[provider.upper()] = api_key
        self._save_api_keys()
    
    def _save_api_keys(self) -> None:
        """保存API密钥到文件"""
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.api_keys_file, "w", encoding="utf-8") as f:
                json.dump(self.api_keys, f, indent=2)
        except Exception as e:
            logging.error(f"保存API密钥文件出错: {e}")
    
    def get_model_config(self, provider: str, model_name: str) -> Dict[str, Any]:
        """获取指定模型的配置
        
        Args:
            provider: 提供商名称，如openai, qwen, deepseek
            model_name: 模型名称，如gpt-3.5-turbo, qwen-plus
            
        Returns:
            Dict[str, Any]: 模型配置，如果不存在则返回空字典
        """
        provider_config = self.models_config.get(provider.lower(), {})
        models = provider_config.get("models", {})
        return models.get(model_name, {})
    
    def get_embedding_model_config(self, provider: str, model_name: str) -> Dict[str, Any]:
        """获取指定嵌入模型的配置
        
        Args:
            provider: 提供商名称，如openai, qwen, deepseek
            model_name: 模型名称，如text-embedding-ada-002
            
        Returns:
            Dict[str, Any]: 嵌入模型配置，如果不存在则返回空字典
        """
        provider_config = self.models_config.get(provider.lower(), {})
        embedding_models = provider_config.get("embedding_models", {})
        return embedding_models.get(model_name, {}) 