from typing import Optional, Dict, Any, Union, List
from openai import OpenAI
from .base import BaseLLMEngine
import os
import random

class DeepSeekEngine(BaseLLMEngine):
    """使用DeepSeek API的LLM引擎，使用OpenAI兼容接口"""
    
    def __init__(self, model_name: str = "deepseek-chat", **kwargs):
        super().__init__(model_name, **kwargs)
        
        # 如果明确指定使用模拟模式，则不需要尝试初始化客户端
        if self.mock_mode:
            self.client = None
            print(f"已启用模拟模式，将使用模拟回复")
            return
        
        # 从环境变量获取API密钥
        self.api_key = kwargs.get("api_key", os.getenv("DEEPSEEK_API_KEY"))
        
        # 如果环境变量中没有，尝试从配置管理器获取
        if not self.api_key:
            try:
                from llm_engine.config.config_manager import ConfigManager
                config = ConfigManager.get_instance()
                self.api_key = config.get_api_key("DEEPSEEK")
            except Exception as e:
                print(f"从配置管理器获取API密钥失败: {e}")
        
        # 检查API密钥是否为占位符或无效格式
        if not self.api_key or self.api_key.startswith("YOUR_") or len(self.api_key) < 10:
            print("警告: DEEPSEEK API密钥无效或为占位符，LLM将以模拟模式运行")
            self.mock_mode = True
            self.client = None
            return
        
        # 初始化OpenAI客户端，使用DeepSeek API
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            # 进行简单测试以验证API密钥有效性
            self._test_api_key()
        except Exception as e:
            print(f"初始化DeepSeek客户端失败，将使用模拟模式: {e}")
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
        """生成文本，支持思考模式
        
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
                if "代码" in prompt or "编程" in prompt:
                    return "这个编程问题需要深入思考。我们可以分步骤解决：1. 分析需求；2. 设计数据结构；3. 实现核心算法；4. 优化代码性能。下面是详细的解决方案..."
                else:
                    return "这个问题很深刻，需要从多个角度思考。首先，我们需要理解问题的本质；其次，我们可以分析可能的解决方案；最后，我们可以评估每种方案的优缺点。"
            else:
                if "代码" in prompt or "编程" in prompt:
                    return "这是一个编程问题，我认为可以使用以下代码解决..."
                else:
                    return "根据我的理解，这个问题的答案是..."
                
        try:
            # 获取系统提示，基于是否使用思考模式
            system_prompt = self._get_system_prompt(think)
            
            # 如果包含编程相关关键词，使用代码优化的系统提示
            if "代码" in prompt or "编程" in prompt or "函数" in prompt or "类" in prompt:
                if think:
                    system_prompt += " 请详细分析编程问题，考虑多种实现方案，分析时间和空间复杂度，并给出最优解决方案。"
                else:
                    system_prompt += " 你是一个编程专家，提供简洁有效的代码解决方案。"
            
            # 获取模型配置参数，优先使用传入的参数，其次使用初始化时加载的配置
            temperature = kwargs.get("temperature", self.temperature)
            top_p = kwargs.get("top_p", self.top_p)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            
            # 使用OpenAI兼容接口调用DeepSeek模型
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            
            # 检查响应是否为None
            if completion is None:
                return "抱歉，服务暂时不可用。"
                
            # 从响应中提取文本
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"生成文本时出错: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我现在无法回答这个问题。"
    
    def get_embeddings(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """获取文本嵌入向量
        
        Args:
            texts: 单个文本字符串或文本列表
            
        Returns:
            嵌入向量或嵌入向量列表
        """
        # 如果是模拟模式，返回模拟的嵌入向量
        if self.mock_mode:
            # 获取嵌入维度，从配置或默认值
            dimensions = self.models_config.get("deepseek", {}).get("embedding_models", {}).get(
                "text-embedding", {}).get("dimensions", 1024)
                
            if isinstance(texts, str):
                return [0.1] * dimensions
            else:
                return [[0.1] * dimensions for _ in texts]
                
        try:
            # 获取嵌入模型名称和维度
            embedding_model = "text-embedding"  # DeepSeek默认嵌入模型
            dimensions = self.models_config.get("deepseek", {}).get("embedding_models", {}).get(
                embedding_model, {}).get("dimensions", 1024)
            
            # 处理单个文本的情况
            if isinstance(texts, str):
                response = self.client.embeddings.create(
                    model=embedding_model,
                    input=texts
                )
                
                # 检查响应是否为None
                if response is None:
                    return [0.0] * dimensions
                
                # 返回嵌入向量
                return response.data[0].embedding
                
            # 处理文本列表的情况
            response = self.client.embeddings.create(
                model=embedding_model,
                input=texts
            )
            
            # 检查响应是否为None
            if response is None:
                return [[0.0] * dimensions for _ in range(len(texts))]
            
            # 返回所有嵌入向量
            return [item.embedding for item in response.data]
            
        except Exception as e:
            print(f"获取文本嵌入时出错: {e}")
            dimensions = self.models_config.get("deepseek", {}).get("embedding_models", {}).get(
                "text-embedding", {}).get("dimensions", 1024)
                
            if isinstance(texts, str):
                return [0.0] * dimensions
            else:
                return [[0.0] * dimensions for _ in range(len(texts))] 