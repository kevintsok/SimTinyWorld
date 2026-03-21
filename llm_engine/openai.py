from typing import Optional, Dict, Any, Union, List
import openai
from .base import BaseLLMEngine
import os
import random

class OpenAIEngine(BaseLLMEngine):
    """OpenAI LLM引擎实现"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(model_name, **kwargs)
        
        # 如果明确指定使用模拟模式，则不需要尝试初始化客户端
        if self.mock_mode:
            self.client = None
            print(f"已启用模拟模式，将使用模拟回复")
            return
        
        # 获取嵌入模型名称，默认为"text-embedding-ada-002"
        self.embedding_model = kwargs.get("embedding_model", 
            self.models_config.get("openai", {}).get("embedding_models", {}).keys())
        if isinstance(self.embedding_model, dict) and len(self.embedding_model) > 0:
            self.embedding_model = list(self.embedding_model)[0]
        elif not isinstance(self.embedding_model, str):
            self.embedding_model = "text-embedding-ada-002"
        
        # 从环境变量获取API密钥
        api_key = kwargs.get("api_key", os.getenv("OPENAI_API_KEY"))
        
        # 如果环境变量中没有，尝试从配置管理器获取
        if not api_key:
            try:
                from llm_engine.config.config_manager import ConfigManager
                config = ConfigManager.get_instance()
                api_key = config.get_api_key("OPENAI")
            except Exception as e:
                print(f"从配置管理器获取API密钥失败: {e}")
        
        # 检查API密钥是否为占位符或无效格式
        if not api_key or api_key.startswith("YOUR_") or len(api_key) < 10:
            print("警告: OPENAI API密钥无效或为占位符，LLM将以模拟模式运行")
            self.mock_mode = True
            self.client = None
            return
        
        # 创建OpenAI客户端
        try:
            self.client = openai.OpenAI(api_key=api_key)
            # 进行简单测试以验证API密钥有效性
            self._test_api_key()
        except Exception as e:
            print(f"初始化OpenAI客户端失败，将使用模拟模式: {e}")
            self.mock_mode = True
            self.client = None
    
    def _test_api_key(self):
        """测试API密钥有效性"""
        try:
            # 尝试一个最小的API调用来验证密钥
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Hello"},
                    {"role": "user", "content": "Hi"}
                ],
                max_tokens=5,
                temperature=0,
                timeout=5  # 设置较短的超时时间
            )
            # 如果没有异常则表示API密钥有效
        except Exception as e:
            print(f"API密钥验证失败: {e}")
            self.mock_mode = True
    
    def generate(self, prompt: str, think: bool = False, **kwargs) -> str:
        """使用OpenAI生成文本，支持思考模式
        
        Args:
            prompt: 输入提示
            think: 是否使用思考模式
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        # 如果是模拟模式，返回一个简单的回复
        if self.mock_mode:
            # 根据思考模式生成不同的模拟回复
            if think:
                return "这是一个值得深入思考的问题。我们可以从多个角度来分析它：首先，...; 其次，...; 最后，综合考虑各方面因素，我认为..."
            else:
                return "这是一个有趣的问题。简单来说，我认为..."
        
        try:
            # 获取系统提示，基于是否使用思考模式
            system_prompt = self._get_system_prompt(think)
            
            # 获取模型配置参数，优先使用传入的参数，其次使用初始化时加载的配置
            temperature = kwargs.get("temperature", self.temperature)
            top_p = kwargs.get("top_p", self.top_p)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            
            # 使用OpenAI客户端生成文本
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                seed=kwargs.get("seed", random.randint(1, 10000))  # 随机种子增加多样性
            )
            
            # 检查响应是否为None
            if response is None:
                return "抱歉，服务暂时不可用。"
                
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"生成文本时出错: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我现在无法回答这个问题。"
    
    def get_embeddings(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """获取文本嵌入
        
        Args:
            texts: 单个文本字符串或文本列表
            
        Returns:
            嵌入向量或嵌入向量列表
        """
        # 如果是模拟模式，返回模拟的嵌入向量
        if self.mock_mode:
            # 获取嵌入维度，从配置或默认值
            dimensions = self.models_config.get("openai", {}).get("embedding_models", {}).get(
                self.embedding_model, {}).get("dimensions", 1536)
                
            if isinstance(texts, str):
                return [0.1] * dimensions
            else:
                return [[0.1] * dimensions for _ in texts]
        
        try:
            # 获取嵌入维度
            dimensions = self.models_config.get("openai", {}).get("embedding_models", {}).get(
                self.embedding_model, {}).get("dimensions", 1536)
            
            # 处理单个文本的情况
            if isinstance(texts, str):
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=texts,
                    dimensions=dimensions
                )
                
                # 检查响应是否为None
                if response is None:
                    return [0.0] * dimensions
                
                # 返回嵌入向量
                return response.data[0].embedding
                
            # 处理文本列表的情况
            # OpenAI API支持批量处理，无需手动分批
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                dimensions=dimensions
            )
            
            # 检查响应是否为None
            if response is None:
                return [[0.0] * dimensions for _ in range(len(texts))]
            
            # 返回所有嵌入向量
            return [item.embedding for item in response.data]
            
        except Exception as e:
            print(f"获取文本嵌入时出错: {e}")
            dimensions = self.models_config.get("openai", {}).get("embedding_models", {}).get(
                self.embedding_model, {}).get("dimensions", 1536)
                
            if isinstance(texts, str):
                return [0.0] * dimensions
            else:
                return [[0.0] * dimensions for _ in range(len(texts))] 