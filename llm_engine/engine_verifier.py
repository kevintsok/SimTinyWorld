from typing import Dict, Any, Optional, List
import os
import time
from colorama import init, Fore, Style
from .factory import LLMEngineFactory

# 初始化colorama
init()

class EngineVerifier:
    """LLM引擎验证器，用于检查和显示各LLM引擎的状态"""
    
    def __init__(self):
        """初始化引擎验证器"""
        self.results = {}
    
    def _get_all_engine_names(self) -> List[str]:
        """
        获取所有注册的引擎名称
        
        Returns:
            List[str]: 所有引擎名称列表
        """
        # 从LLMEngineFactory获取所有可用引擎名称
        return list(LLMEngineFactory.get_available_engines().keys())
    
    def verify_all_engines(self, check_actual_api: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        验证所有引擎的状态
        
        Args:
            check_actual_api: 是否执行实际的API调用来验证
            
        Returns:
            Dict[str, Dict[str, Any]]: 引擎状态信息
        """
        try:
            # 尝试获取所有引擎的验证结果
            self.results = LLMEngineFactory.verify_engines(check_actual_api)
            return self.results
        except Exception as e:
            print(f"验证引擎时出现错误: {e}")
            # 确保即使出现异常也始终返回结果
            try:
                engines = self._get_all_engine_names()
            except Exception:
                # 如果连引擎名称都无法获取，使用备用方案
                engines = ["qwen", "dashscope", "openai", "azure", "gemini", "anthropic", "deepseek"]
            
            self.results = {}
            for engine_name in engines:
                self.results[engine_name] = {
                    "available": False,
                    "mock_mode": True,
                    "error": f"验证过程出错: {str(e)}",
                    "models": []
                }
            return self.results
    
    def display_status(self) -> None:
        """打印引擎状态信息到控制台，带颜色标记"""
        if not self.results:
            self.verify_all_engines(check_actual_api=False)
        
        print(f"\n{Fore.CYAN}===== LLM引擎状态 ====={Style.RESET_ALL}")
        print(f"检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        for engine_name, status in self.results.items():
            # 确定引擎状态的颜色
            if status["available"]:
                status_color = Fore.GREEN
                status_text = "可用"
            else:
                if status["mock_mode"]:
                    status_color = Fore.YELLOW
                    status_text = "模拟模式"
                else:
                    status_color = Fore.RED
                    status_text = "不可用"
            
            # 打印引擎名称和状态
            print(f"{Fore.WHITE}引擎: {Fore.BLUE}{engine_name}{Style.RESET_ALL}")
            print(f"状态: {status_color}{status_text}{Style.RESET_ALL}")
            
            # 如果有错误，显示错误信息
            if status["error"]:
                print(f"错误: {Fore.RED}{status['error']}{Style.RESET_ALL}")
            
            # 显示支持的模型
            if status["models"]:
                print(f"支持的模型: {', '.join(status['models'])}")
            
            print("-" * 60)
    
    def get_first_available_engine(self) -> Optional[str]:
        """
        获取第一个可用的引擎名称
        
        Returns:
            Optional[str]: 可用引擎名称，如果没有可用的引擎则返回None
        """
        if not self.results:
            self.verify_all_engines(check_actual_api=False)
        
        for engine_name, status in self.results.items():
            if status["available"]:
                return engine_name
        
        # 如果没有真正可用的引擎，返回第一个模拟模式的引擎
        for engine_name, status in self.results.items():
            if status["mock_mode"]:
                return engine_name
        
        return None
    
    def is_engine_available(self, engine_name: str) -> bool:
        """
        检查指定引擎是否可用
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            bool: 是否可用
        """
        if not self.results:
            self.verify_all_engines(check_actual_api=False)
        
        status = self.results.get(engine_name.lower(), {})
        return status.get("available", False)
    
    def get_available_engines(self) -> List[str]:
        """
        获取所有可用的引擎名称列表
        
        Returns:
            List[str]: 可用引擎名称列表
        """
        if not self.results:
            self.verify_all_engines(check_actual_api=False)
        
        return [
            engine_name for engine_name, status in self.results.items()
            if status["available"]
        ]
    
    def get_engines_in_mock_mode(self) -> List[str]:
        """
        获取所有处于模拟模式的引擎名称列表
        
        Returns:
            List[str]: 模拟模式引擎名称列表
        """
        if not self.results:
            self.verify_all_engines(check_actual_api=False)
        
        return [
            engine_name for engine_name, status in self.results.items()
            if status["mock_mode"] and not status["available"]
        ] 