from typing import Optional, Dict, Any, Union, List
from openai import OpenAI
from .base import BaseLLMEngine
import os
import random

class QwenEngine(BaseLLMEngine):
    """使用阿里云通义千问API的LLM引擎，使用OpenAI兼容接口
    
    API文档: https://help.aliyun.com/zh/dashscope/developer-reference/api-details
    """
    
    def __init__(self, model_name: str = "qwen3.5-flash", **kwargs):
        super().__init__(model_name, **kwargs)
        
        # 如果明确指定使用模拟模式，则不需要尝试初始化客户端
        if self.mock_mode:
            self.client = None
            print(f"已启用模拟模式，将使用模拟回复")
            return
        
        self.api_key = kwargs.get("api_key", os.getenv("DASHSCOPE_API_KEY"))

        if not self.api_key:
            try:
                from llm_engine.config.config_manager import ConfigManager
                config = ConfigManager.get_instance()
                self.api_key = config.get_api_key("QWEN")
            except Exception as e:
                print(f"从配置管理器获取API密钥失败: {e}")
        
        if not self.api_key or self.api_key.startswith("YOUR_") or len(self.api_key) < 10:
            print("警告: QWEN API密钥无效或为占位符，LLM将以模拟模式运行")
            self.mock_mode = True
            self.client = None
            return
        
        base_url = self.models_config.get("qwen", {}).get("base_url",
                 "https://dashscope.aliyuncs.com/compatible-mode/v1")

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
            self._test_api_key()
        except Exception as e:
            print(f"初始化Qwen客户端失败，将使用模拟模式: {e}")
            self.mock_mode = True
            self.client = None
    
    def _test_api_key(self):
        """测试API密钥有效性"""
        try:
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Hello"},
                    {"role": "user", "content": "Hi"}
                ],
                max_tokens=5,
                temperature=0,
                timeout=5
            )
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
                return "这个问题需要深入思考。首先，我们应该分析问题的核心。接着，考虑各种可能的方案和实现方式。最后，综合各方面因素，得出合理的结论和建议。"
            
            # 根据提示中可能包含的问题类型生成不同的模拟回复
            if "开场白" in prompt or "打招呼" in prompt:
                return "你好！这里环境很不错，我们可以聊聊吗？"
            elif "告别" in prompt or "道别" in prompt:
                return "时间不早了，我得先走了。下次再聊！"
            else:
                return "。"
                
        try:
            # 获取系统提示，基于是否使用思考模式
            system_prompt = self._get_system_prompt(think)
            
            # 获取模型配置参数，优先使用传入的参数，其次使用初始化时加载的配置
            temperature = kwargs.get("temperature", self.temperature)
            top_p = kwargs.get("top_p", self.top_p)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            
            # 使用OpenAI兼容接口调用通义千问模型
            completion = self.client.chat.completions.create(
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
            dimensions = self.models_config.get("qwen", {}).get("embedding_models", {}).get(
                "text-embedding-v3", {}).get("dimensions", 1024)
                
            if isinstance(texts, str):
                return [0.1] * dimensions
            else:
                return [[0.1] * dimensions for _ in texts]
                
        try:
            # 获取嵌入模型名称和维度
            embedding_model = "text-embedding-v3"  # 通义千问默认嵌入模型
            dimensions = self.models_config.get("qwen", {}).get("embedding_models", {}).get(
                embedding_model, {}).get("dimensions", 1024)
            
            # 处理单个文本的情况
            if isinstance(texts, str):
                response = self.client.embeddings.create(
                    model=embedding_model,
                    input=texts,
                    dimensions=dimensions,
                    encoding_format="float"
                )
                
                # 检查响应是否为None
                if response is None:
                    return [0.0] * dimensions
                
                # 返回嵌入向量
                return response.data[0].embedding
                
            # 处理文本列表的情况，确保批量不超过10
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                response = self.client.embeddings.create(
                    model=embedding_model,
                    input=batch_texts,
                    dimensions=dimensions,
                    encoding_format="float"
                )
                
                # 检查响应是否为None
                if response is None:
                    all_embeddings.extend([[0.0] * dimensions for _ in range(len(batch_texts))])
                    continue
                
                # 将当前批次的嵌入向量添加到结果中
                all_embeddings.extend([item.embedding for item in response.data])
            
            # 返回所有嵌入向量
            return all_embeddings
            
        except Exception as e:
            print(f"获取文本嵌入时出错: {e}")
            dimensions = self.models_config.get("qwen", {}).get("embedding_models", {}).get(
                "text-embedding-v3", {}).get("dimensions", 1024)
                
            if isinstance(texts, str):
                return [0.0] * dimensions
            else:
                return [[0.0] * dimensions for _ in range(len(texts))] 