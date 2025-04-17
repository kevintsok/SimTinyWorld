from typing import Optional, Dict, Any, Union, List
from openai import OpenAI
from .base import BaseLLMEngine
from config.config_manager import ConfigManager
import os
import random

class QwenEngine(BaseLLMEngine):
    """使用阿里云通义千问API的LLM引擎，使用OpenAI兼容接口
    
    API文档: https://help.aliyun.com/zh/dashscope/developer-reference/api-details
    """
    
    def __init__(self, model_name: str = "qwen-plus", **kwargs):
        super().__init__(model_name, **kwargs)
        
        # 确保mock_mode属性有一个初始值
        self.mock_mode = False
        
        # 优先从参数获取API密钥，其次从环境变量，最后从配置管理器
        self.api_key = kwargs.get("api_key", os.getenv("DASHSCOPE_API_KEY"))
        
        # 如果以上方式都没有获得API密钥，尝试从配置管理器获取
        if not self.api_key:
            try:
                config = ConfigManager.get_instance()
                self.api_key = config.get_api_key("QWEN")
            except Exception as e:
                print(f"从配置管理器获取API密钥失败: {e}")
        
        # 如果仍然没有API密钥，使用模拟模式
        if not self.api_key:
            # 为了方便测试，如果没有API密钥，使用模拟模式
            print("警告: 未找到DASHSCOPE_API_KEY，LLM将以模拟模式运行")
            self.mock_mode = True
            self.client = None
        else:
            # 初始化OpenAI客户端
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        
        # 设置生成参数
        self.temperature = kwargs.get("temperature", 0.8)  # 增加温度以提高输出多样性
        self.top_p = kwargs.get("top_p", 0.9)  # 保留一定随机性
        self.max_tokens = kwargs.get("max_tokens", 4096)
        
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        # 如果是模拟模式，返回一个简单的回复
        if hasattr(self, 'mock_mode') and self.mock_mode:
            # 根据提示中可能包含的问题类型生成不同的模拟回复
            if "开场白" in prompt or "打招呼" in prompt:
                return "你好！这里环境很不错，我们可以聊聊吗？"
            elif "告别" in prompt or "道别" in prompt:
                return "时间不早了，我得先走了。下次再聊！"
            else:
                return "这个问题很有趣，我需要好好思考一下。"
                
        try:
            # 使用OpenAI兼容接口调用通义千问模型
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", self.temperature),
                top_p=kwargs.get("top_p", self.top_p),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                seed=random.randint(1, 10000)  # 随机种子增加多样性
            )
            
            # 检查响应是否为None
            if completion is None:
                return "抱歉，服务暂时不可用。"
                
            # 从响应中提取文本
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"生成文本时出错: {e}")
            # print traceback
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
        if hasattr(self, 'mock_mode') and self.mock_mode:
            if isinstance(texts, str):
                return [0.1] * 1024  # 返回1024维的向量
            else:
                return [[0.1] * 1024 for _ in texts]  # 为每个文本返回1024维的向量
                
        try:
            # 处理单个文本的情况
            if isinstance(texts, str):
                response = self.client.embeddings.create(
                    model="text-embedding-v3",
                    input=texts,
                    dimensions=1024,
                    encoding_format="float"
                )
                
                # 检查响应是否为None
                if response is None:
                    return [0.0] * 1024  # 返回零向量
                
                # 返回嵌入向量
                return response.data[0].embedding
                
            # 处理文本列表的情况，确保批量不超过10
            # 分批处理
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                response = self.client.embeddings.create(
                    model="text-embedding-v3",
                    input=batch_texts,
                    dimensions=1024,
                    encoding_format="float"
                )
                
                # 检查响应是否为None
                if response is None:
                    all_embeddings.extend([[0.0] * 1024 for _ in range(len(batch_texts))])
                    continue
                
                # 将当前批次的嵌入向量添加到结果中
                all_embeddings.extend([item.embedding for item in response.data])
            
            # 返回所有嵌入向量
            return all_embeddings
            
        except Exception as e:
            print(f"获取文本嵌入时出错: {e}")
            if isinstance(texts, str):
                # 返回一个空向量作为备选
                return [0.0] * 1024  # 通义文本嵌入维度通常是1024
            else:
                # 返回一个空向量列表作为备选
                return [[0.0] * 1024 for _ in range(len(texts))] 