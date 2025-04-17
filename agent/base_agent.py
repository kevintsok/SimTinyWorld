import os
import uuid
import json
import time
import random
from typing import List, Dict, Optional, Any, Sequence
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.embeddings import Embeddings
from llm_engine.factory import LLMEngineFactory

class Memory(BaseModel):
    content: str
    timestamp: float
    importance: float

class LLMEngineEmbeddings(Embeddings):
    """将LLM引擎的嵌入功能包装为LangChain Embeddings对象"""
    
    def __init__(self, llm_engine):
        self.llm_engine = llm_engine
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """对多个文本进行嵌入"""
        return self.llm_engine.get_embeddings(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """对单个查询文本进行嵌入"""
        return self.llm_engine.get_embeddings(text)

class BaseAgent:
    def __init__(self, name: Optional[str] = None, llm_engine_type: str = "qwen", gender: Optional[str] = None, **llm_kwargs):
        self.id = str(uuid.uuid4())
        self.name = name or f"Agent_{self.id[:8]}"
        self.mbti = self._generate_random_mbti()
        self.background = self._generate_background(gender=gender)
        self.long_term_memory: List[str] = []
        self.short_term_memory: List[str] = []
        
        # 初始化存储目录
        self.memory_dir = f"agent/history/{self.id}"
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 初始化记忆文件
        self.longterm_file = f"{self.memory_dir}/long.txt"
        self.shortterm_file = f"{self.memory_dir}/short.txt"
        
        # 初始化LLM引擎
        self.llm_engine = LLMEngineFactory.create_engine(llm_engine_type, **llm_kwargs)
        
        # 生成外貌描述
        self.appearance = self._generate_appearance()
        
        # 如果文件存在，加载记忆
        self._load_memories()
        
        # 创建Embeddings对象
        self.embeddings = LLMEngineEmbeddings(self.llm_engine)
        
        # 初始化向量存储
        self.text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.vector_store = None
        self._update_vector_store()
        
    def _generate_random_mbti(self) -> str:
        # 简单实现，后续可以扩展
        mbti_types = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                     "ISTJ", "ISTP", "ESTJ", "ESTP", "ISFJ", "ISFP", "ESFJ", "ESFP"]
        return random.choice(mbti_types)
    
    def _generate_background(self, gender: Optional[str] = None) -> Dict:
        # 如果外部指定了性别，使用指定的性别；否则随机生成
        if gender not in ["男", "女"]:
            gender = random.choice(["男", "女"])
            
        return {
            "age": random.randint(18, 80),
            "gender": gender,
            "occupation": random.choice(["工程师", "教师", "医生", "艺术家", "学生"]),
            "education": random.choice(["高中", "本科", "硕士", "博士"]),
            "hometown": random.choice(["北京", "上海", "广州", "深圳", "成都"])
        }
    
    def _generate_appearance(self) -> str:
        """根据智能体的属性使用LLM生成外貌描述"""
        # 如果LLM引擎还没有初始化，返回一个占位符
        if not hasattr(self, 'llm_engine'):
            return "外表普通，没有特别突出的特征。"
            
        # 构建提示，基于智能体的基本属性
        prompt = f"""
作为一位角色外貌描述生成器，请为以下角色生成一段简短的外貌描述（50-80字）。

角色信息:
- 姓名: {self.name}
- 性别: {self.background['gender']}
- 年龄: {self.background['age']}岁
- 职业: {self.background['occupation']}
- MBTI: {self.mbti}

描述要求:
1. 包含体型、面部特征、发型、眼睛等基本外貌特征
2. 描述要和角色的职业、年龄、性格(MBTI)相符
3. 风格要自然、具体，能让人想象出角色的样子
4. 不要包含价值判断，保持中立描述
5. 只描述外表，不要描述性格或心理特征
6. 长度控制在50-80字之间

请直接给出描述，不要有任何多余的解释或格式，也不要用引号包裹。
"""
        
        try:
            # 获取LLM生成的外貌描述
            response = self.llm_engine.generate(prompt)
            
            # 确保response不为None
            appearance = response.strip() if response else ""
            
            # 如果返回为空，使用默认描述
            if not appearance:
                default_descriptions = self._get_default_appearance_descriptions()
                return random.choice(default_descriptions)
                
            return appearance
        except Exception as e:
            print(f"生成外貌描述时出错: {e}")
            default_descriptions = self._get_default_appearance_descriptions()
            return random.choice(default_descriptions)
            
    def _get_default_appearance_descriptions(self) -> List[str]:
        """获取默认的外貌描述列表"""
        if self.background['gender'] == "男":
            return [
                f"{self.name}身材{random.choice(['高大', '中等', '偏瘦'])}，{random.choice(['浓眉大眼', '五官端正', '眉清目秀'])}，{random.choice(['短发利落', '头发略长但整齐', '寸头干练'])}，穿着{random.choice(['简洁大方', '休闲随意', '正式得体'])}，给人{random.choice(['可靠', '亲切', '严肃', '专业'])}的印象。",
                f"一位{random.choice(['英俊', '普通', '朴实'])}的{self.background['age']}岁男性，{random.choice(['肤色健康', '肤色偏白', '肤色小麦色'])}，{random.choice(['戴着眼镜', '眼神专注', '目光炯炯'])}，穿着符合{self.background['occupation']}身份的{random.choice(['正装', '休闲服', '职业装'])}。",
                f"{random.choice(['中等身材', '挺拔身材', '偏瘦身材'])}的男子，{random.choice(['面容清秀', '面容和善', '轮廓分明'])}，{random.choice(['显得精神焕发', '透露出职业特色', '举止自然得体'])}，是典型的{self.background['occupation']}形象。"
            ]
        else:
            return [
                f"{self.name}身材{random.choice(['苗条', '中等', '娇小'])}，{random.choice(['面容姣好', '五官精致', '气质清新'])}，{random.choice(['长发飘逸', '短发利落', '发型时尚大方'])}，穿着{random.choice(['典雅', '简约', '活泼'])}，举止{random.choice(['优雅', '得体', '自然'])}。",
                f"一位{random.choice(['气质优雅', '朴实无华', '活力四射'])}的{self.background['age']}岁女性，{random.choice(['肤色白皙', '肤色健康', '肤色红润'])}，{random.choice(['双眼有神', '目光温和', '笑容亲切'])}，装扮体现了{self.background['occupation']}的职业特点。",
                f"{random.choice(['窈窕', '匀称', '纤细'])}的女子，{random.choice(['气质温婉', '精神爽朗', '举止大方'])}，{random.choice(['发型整洁', '妆容淡雅', '着装得体'])}，让人一眼就能感受到她作为{self.background['occupation']}的专业气质。"
            ]
    
    def _load_memories(self):
        """加载记忆文件中的内容到内存"""
        # 加载长期记忆
        self.long_term_memory = []
        if os.path.exists(self.longterm_file):
            with open(self.longterm_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    memories = content.split("\n")
                    for mem_str in memories:
                        if mem_str.strip():
                            self.long_term_memory.append(mem_str)
        
        # 加载短期记忆
        self.short_term_memory = []
        if os.path.exists(self.shortterm_file):
            with open(self.shortterm_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    memories = content.split("\n")
                    for mem_str in memories:
                        if mem_str.strip():
                            self.short_term_memory.append(mem_str)
    
    def _update_vector_store(self):
        """更新向量存储"""
        if not self.long_term_memory:
            return
            
        # 获取所有记忆的文本
        texts = self.long_term_memory
        
        # 使用FAISS正确的创建方式 - 通过Embeddings对象
        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings
        )
    
    def add_memory(self, content: str, is_long_term: bool = False, importance: float = 0.5):
        """添加记忆
        
        Args:
            content: 记忆内容
            is_long_term: 是否为长期记忆，默认为False（短期记忆）
            importance: 重要性评分，范围0-1，默认0.5（不再使用）
        """
        # 所有记忆都添加到短期记忆文件
        self._save_to_short_memory(content)
        
        # 如果是长期记忆，则同时保存到长期记忆中
        if is_long_term:
            self._save_to_long_memory(content)
            self._update_vector_store()
    
    def _save_to_short_memory(self, content: str):
        """保存记忆到短期记忆文件，以纯文本格式"""
        # 将记忆以纯文本格式追加到短期记忆文件末尾
        with open(self.shortterm_file, "a", encoding="utf-8") as f:
            if os.path.getsize(self.shortterm_file) > 0:
                f.write("\n")
            f.write(content)
    
    def _save_to_long_memory(self, content: str):
        """保存记忆到长期记忆文件，以纯文本格式"""
        # 将记忆以纯文本格式追加到长期记忆文件末尾
        with open(self.longterm_file, "a", encoding="utf-8") as f:
            if os.path.getsize(self.longterm_file) > 0:
                f.write("\n")
            f.write(content)
    
    def query_memory(self, query: str) -> str:
        """根据提供的查询生成回复，支持真实LLM和模拟模式
        
        Args:
            query: 查询/提示文本
            
        Returns:
            str: 生成的回复
        """
        # 检测是否处于模拟模式
        is_mock_mode = hasattr(self.llm_engine, 'mock_mode') and self.llm_engine.mock_mode
        
        # 从长期记忆中检索相关信息
        relevant_docs = []
        if self.vector_store:
            try:
                relevant_docs = self.vector_store.similarity_search(query, k=3)
            except Exception as e:
                print(f"查询记忆时出错: {e}")
        
        # 构建上下文
        context = "\n".join([doc.page_content for doc in relevant_docs]) if relevant_docs else ""
        
        # 获取最近的记忆（假设最近添加的在列表末尾）
        recent_memories_count = min(5, len(self.short_term_memory))
        recent_memories = "\n".join(self.short_term_memory[-recent_memories_count:])
        
        # MBTI性格特点描述
        mbti_descriptions = {
            "INTJ": "独立、逻辑性强、善于战略思考、直接坦率、有时显得冷漠",
            "INTP": "好奇心强、理性分析、喜欢理论探讨、独立思考、可能显得冷淡",
            "ENTJ": "自信果断、善于领导、直接坦率、追求效率、可能显得专横",
            "ENTP": "创新、辩论爱好者、机智幽默、思维灵活、可能显得争辩",
            "INFJ": "有洞察力、理想主义、重视和谐、有同理心、可能显得神秘",
            "INFP": "理想主义、富有同情心、创意丰富、重视真实性、可能显得沉默",
            "ENFJ": "温暖、善解人意、善于激励他人、社交能力强、可能显得过度关心",
            "ENFP": "热情、创意丰富、善于交际、思维开放、可能显得注意力不集中",
            "ISTJ": "实际、可靠、条理分明、尊重传统、可能显得固执",
            "ISTP": "灵活、实用主义、独立、喜欢解决问题、可能显得冷漠",
            "ESTJ": "有组织能力、务实、注重秩序、负责任、可能显得专制",
            "ESTP": "活力充沛、冒险家、享受当下、适应力强、可能显得鲁莽",
            "ISFJ": "体贴、负责任、注重细节、忠诚、可能显得过度担忧",
            "ISFP": "和平主义者、敏感、艺术气质、注重和谐、可能显得被动",
            "ESFJ": "友好、合作、重视他人需求、善于照顾、可能显得多管闲事",
            "ESFP": "热情、外向、享受生活、自发性强、可能显得寻求关注"
        }
        
        mbti_traits = mbti_descriptions.get(self.mbti, "独特的性格特点")
        
        # 构建提示模板
        prompt = f"""基于以下信息，以{self.name}({self.mbti})的身份生成回应：

关于{self.name}:
- 性格: {self.mbti}，特点: {mbti_traits}
- 性别: {self.background['gender']}
- 职业: {self.background['occupation']}
- 年龄: {self.background['age']}岁
- 来自: {self.background['hometown']}
- 教育: {self.background['education']}
- 外貌: {self.appearance}

长期记忆中的相关信息：
{context}

最近的记忆：
{recent_memories}

请求/问题：{query}

回应要求：
1. 你必须完全根据{self.name}的性格({self.mbti})和背景进行回答
2. 回答应当展现出{mbti_traits}的特质
3. 避免任何形式的重复套话或通用问候
4. 避免简单自我介绍（如"你好，我是XXX"）
5. 在回答中适当提及环境或场景的特点
6. 展现出对当前情境的感知和情绪反应
7. 如果对话发生在特定场所，表现出对该场所的了解和反应

语言要求：
- 回答长度应为20-40字，既不过短也不冗长
- 语言自然流畅，符合日常对话风格
- 表达要有个性，让人感觉是真实的{self.name}在说话

请现在以{self.name}的身份生成回应：
"""
        
        # 使用LLM引擎生成回答
        response = self.llm_engine.generate(prompt)
        
        # 确保返回有效字符串
        if response is None or response.strip() == "":
            # 使用更简化的提示重试
            simplified_prompt = f"""作为{self.name}，一个{self.background['gender']}性{self.background['age']}岁{self.background['occupation']}，请生成一句对话回应。

你的MBTI类型是{self.mbti}，主要特点是{mbti_traits}。
你需要回应的内容是: {query}

请注意：
1. 你是{self.name}，不是AI，不是助手
2. 回答必须完全符合{self.mbti}性格类型特点
3. {'表现得外向、积极、社交' if self.mbti.startswith('E') else '表现得内向、深思熟虑、独立'}
4. 回答必须在20-40字之间，简洁自然
5. 必须用第一人称，像真实对话一样

直接生成回应，不要加任何前缀或格式："""
            
            # 重试生成回答
            response = self.llm_engine.generate(simplified_prompt)
            
            # 如果仍然失败，尝试更简单的提示
            if response is None or response.strip() == "":
                minimal_prompt = f"你是{self.name}，请对'{query}'做出不超过20字的自然回应。"
                response = self.llm_engine.generate(minimal_prompt)
                
                # 最后一次尝试
                if response is None or response.strip() == "":
                    final_prompt = f"给出一个简短的回应（10-15字）："
                    response = self.llm_engine.generate(final_prompt)
        
        return response.strip() if response else ""

    def save_identity(self, directory: str = "agent/history"):
        """保存智能体的身份信息到指定目录
        
        Args:
            directory: 保存目录，默认为agent/history
        """
        # 创建智能体ID对应的目录
        agent_dir = f"{directory}/{self.id}"
        os.makedirs(agent_dir, exist_ok=True)
        
        # 构建身份信息
        identity = {
            "id": self.id,
            "name": self.name,
            "mbti": self.mbti,
            "background": self.background,
            "appearance": self.appearance,
            "creation_time": time.time()
        }
        
        # 保存到identity.txt文件
        with open(f"{agent_dir}/identity.txt", "w", encoding="utf-8") as f:
            json.dump(identity, f, ensure_ascii=False, indent=2)
            
    @classmethod
    def load_from_id(cls, agent_id: str, directory: str = "agent/history", **llm_kwargs):
        """从保存的ID加载智能体
        
        Args:
            agent_id: 智能体ID
            directory: 保存目录，默认为agent/history
            **llm_kwargs: LLM引擎的初始化参数
            
        Returns:
            BaseAgent: 加载的智能体实例
        """
        identity_file = f"{directory}/{agent_id}/identity.txt"
        if not os.path.exists(identity_file):
            raise ValueError(f"找不到ID为{agent_id}的智能体身份信息")
            
        # 加载身份信息
        with open(identity_file, "r", encoding="utf-8") as f:
            identity = json.load(f)
        
        # 创建一个没有初始化的实例
        agent = cls.__new__(cls)
        
        # 手动设置属性，避免调用__init__生成新ID
        agent.id = agent_id
        agent.name = identity["name"]
        agent.mbti = identity["mbti"]
        agent.background = identity["background"]
        agent.long_term_memory = []
        agent.short_term_memory = []
        
        # 加载外貌信息
        if "appearance" in identity:
            agent.appearance = identity["appearance"]
        else:
            # 初始化LLM引擎，用于生成外貌
            agent.llm_engine = LLMEngineFactory.create_engine(llm_kwargs.get("llm_engine_type", "qwen"), **llm_kwargs)
            agent.appearance = agent._generate_appearance()
        
        # 设置记忆目录和文件路径
        agent.memory_dir = f"{directory}/{agent_id}"
        agent.longterm_file = f"{agent.memory_dir}/long.txt"
        agent.shortterm_file = f"{agent.memory_dir}/short.txt"
        
        # 初始化LLM引擎（如果尚未初始化）
        if not hasattr(agent, 'llm_engine'):
            agent.llm_engine = LLMEngineFactory.create_engine(llm_kwargs.get("llm_engine_type", "qwen"), **llm_kwargs)
        
        # 加载记忆
        agent._load_memories()
        
        # 创建Embeddings对象
        agent.embeddings = LLMEngineEmbeddings(agent.llm_engine)
        
        # 初始化向量存储
        agent.text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        agent.vector_store = None
        agent._update_vector_store()
        
        return agent
        
    @classmethod
    def get_all_saved_agents(cls, directory: str = "agent/history"):
        """获取所有保存的智能体ID
        
        Args:
            directory: 保存目录，默认为agent/history
            
        Returns:
            List[Dict]: 所有保存的智能体信息列表
        """
        agents = []
        
        if not os.path.exists(directory):
            return agents
            
        for agent_id in os.listdir(directory):
            identity_file = f"{directory}/{agent_id}/identity.txt"
            if os.path.exists(identity_file):
                try:
                    with open(identity_file, "r", encoding="utf-8") as f:
                        identity = json.load(f)
                        agents.append(identity)
                except:
                    pass
                    
        return agents 