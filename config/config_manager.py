import os
from typing import Dict, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config/api_keys.txt"):
        self.config_file = config_file
        self.api_keys: Dict[str, str] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        self.api_keys[key.strip()] = value.strip()
                    except ValueError:
                        continue
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        获取指定服务的API密钥
        
        Args:
            service: 服务名称（如 'QWEN', 'OPENAI', 'DEEPSEEK'）
        
        Returns:
            str: API密钥，如果不存在则返回None
        """
        key = f"{service.upper()}_API_KEY"
        return self.api_keys.get(key)
    
    def get_all_api_keys(self) -> Dict[str, str]:
        """获取所有API密钥"""
        return self.api_keys.copy()
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """获取单例实例"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance 