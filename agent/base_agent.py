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
        
        # 设置记忆容量限制
        self.max_short_term_memories = 50  # 短期记忆条目上限
        self.max_long_term_memories = 200   # 长期记忆条目上限
        
        # 计划和状态
        self.daily_plan = []  # 每日计划列表
        self.status = "休息中"  # 当前状态
        self.current_plan_index = 0  # 当前执行的计划索引
        
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
        
        # 初始化财富属性
        self.wealth = self._generate_wealth()
        
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
            
        # 更新内存中的短期记忆
        self.short_term_memory.append(content)
        
        # 管理短期记忆容量
        self._manage_short_term_memory()
    
    def _manage_short_term_memory(self):
        """管理短期记忆容量，确保不超过最大限制"""
        # 如果短期记忆超过最大限制，删除最早的记忆
        if len(self.short_term_memory) > self.max_short_term_memories:
            # 保留最新的记忆
            self.short_term_memory = self.short_term_memory[-self.max_short_term_memories:]
            
            # 更新短期记忆文件
            with open(self.shortterm_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.short_term_memory))
    
    def _manage_long_term_memory(self):
        """管理长期记忆容量，确保不超过最大限制"""
        # 如果长期记忆超过最大限制，删除最早的记忆
        if len(self.long_term_memory) > self.max_long_term_memories:
            # 保留最新的记忆
            self.long_term_memory = self.long_term_memory[-self.max_long_term_memories:]
            
            # 更新长期记忆文件
            with open(self.longterm_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.long_term_memory))
            
            # 更新向量存储
            self._update_vector_store()
            
    def _save_to_long_memory(self, content: str):
        """保存记忆到长期记忆文件，以纯文本格式"""
        # 将记忆以纯文本格式追加到长期记忆文件末尾
        with open(self.longterm_file, "a", encoding="utf-8") as f:
            if os.path.getsize(self.longterm_file) > 0:
                f.write("\n")
            f.write(content)
    
    def respone(self, query: str) -> str:
        """根据提供的查询生成回复，结合当前状态和角色特点
        
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
        
        # 状态相关的行为和情绪特点
        status_traits = {
            "工作中": "专注、严谨、思考型、寻求效率、解决问题导向",
            "放松中": "轻松、开放、情绪平和、随意、乐于交流",
            "用餐中": "愉快、社交、分享、放松、感官享受",
            "社交中": "友好、热情、互动、关注他人、外向",
            "观察中": "好奇、细心、分析、安静、思考",
            "探索中": "冒险、好奇、主动、寻求新知、兴奋",
            "休息中": "平静、内省、恢复能量、放松、舒适",
            "学习中": "专注、好奇、分析、吸收新知、积极思考",
            "活动中": "精力充沛、积极、投入、专注、执行导向"
        }
        
        # 获取当前状态的特点，如果状态不在预定义列表中，则使用通用描述
        status_trait = status_traits.get(self.status, "处于当前状态的特点")
        
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
- 当前状态: {self.status}，表现特点: {status_trait}

长期记忆中的相关信息：
{context}

最近的记忆：
{recent_memories}

请求/问题：{query}

回应要求：
1. 你必须完全根据{self.name}的性格({self.mbti})和背景进行回答
2. 回答应当体现当前状态({self.status})下的情绪和行为特点
3. 回答应当展现出{mbti_traits}的特质
4. 避免任何形式的重复套话或通用问候
5. 避免简单自我介绍（如"你好，我是XXX"）
6. 在回答中适当提及环境或场景的特点
7. 展现出对当前情境的感知和情绪反应
8. 如果对话发生在特定场所，表现出对该场所的了解和反应

语言要求：
- 回答长度应为20-40字，既不过短也不冗长
- 语言自然流畅，符合日常对话风格
- 表达要有个性，让人感觉是真实的{self.name}在说话

请现在以{self.name}({self.status})的身份生成回应：
"""
        
        # 使用LLM引擎生成回答
        response = self.llm_engine.generate(prompt)
        
        # 确保返回有效字符串
        if response is None or response.strip() == "":
            # 使用更简化的提示重试
            simplified_prompt = f"""作为{self.name}，一个{self.background['gender']}性{self.background['age']}岁{self.background['occupation']}，目前状态是{self.status}，请生成一句对话回应。

你的MBTI类型是{self.mbti}，主要特点是{mbti_traits}。
当前状态({self.status})的表现特点: {status_trait}
你需要回应的内容是: {query}

请注意：
1. 你是{self.name}，不是AI，不是助手
2. 回答必须完全符合{self.mbti}性格类型特点
3. {'表现得外向、积极、社交' if self.mbti.startswith('E') else '表现得内向、深思熟虑、独立'}
4. 回答必须在20-40字之间，简洁自然
5. 必须用第一人称，像真实对话一样
6. 体现当前状态({self.status})的特点

直接生成回应，不要加任何前缀或格式："""
            
            # 重试生成回答
            response = self.llm_engine.generate(simplified_prompt)
            
            # 如果仍然失败，尝试更简单的提示
            if response is None or response.strip() == "":
                minimal_prompt = f"你是{self.name}，正在{self.status}，请对'{query}'做出不超过20字的自然回应。"
                response = self.llm_engine.generate(minimal_prompt)
                
                # 最后一次尝试
                if response is None or response.strip() == "":
                    final_prompt = f"给出一个简短的回应（10-15字）："
                    response = self.llm_engine.generate(final_prompt)
        
        return response.strip() if response else ""

    # 兼容性保持 - 旧方法指向新方法
    def query_memory(self, query: str) -> str:
        """为兼容性保留的方法，重定向到respone方法"""
        return self.respone(query)

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
            "wealth": self.wealth,
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
            
        # 加载财富信息
        if "wealth" in identity:
            agent.wealth = identity["wealth"]
        else:
            # 初始化LLM引擎，用于生成财富
            if not hasattr(agent, 'llm_engine'):
                agent.llm_engine = LLMEngineFactory.create_engine(llm_kwargs.get("llm_engine_type", "qwen"), **llm_kwargs)
            agent.wealth = agent._generate_wealth()
        
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

    def sleep(self) -> None:
        """每天结束时调用，处理短期记忆并将重要内容存入长期记忆
        
        过程:
        1. 分析短期记忆并提取重要信息
        2. 将重要信息存入长期记忆
        3. 管理记忆容量，确保不超过最大限制
        4. 反思今天的计划完成情况
        
        Returns:
            None
        """
        # 如果没有短期记忆，直接返回
        if not self.short_term_memory:
            return
        
        # 反思当天计划完成情况
        reflection = self._reflect_on_daily_plan()
        if reflection:
            # 将反思记录到短期记忆
            self.add_memory(reflection)
            
        # 构建提示，用于分析短期记忆
        memories_text = "\n".join(self.short_term_memory)
        prompt = f"""作为{self.name}({self.mbti})，请分析以下今天的经历，并总结最值得记住的3-5条记忆：

今天的经历:
{memories_text}

请根据以下标准评估哪些记忆最重要:
1. 对个人成长的影响
2. 涉及重要人际关系的事件
3. 情感强度高的体验
4. 与重要目标相关的进展
5. 特别的新信息或洞察

对于你({self.name})这样一个{self.background['gender']}性、{self.background['age']}岁{self.background['occupation']}，具有{self.mbti}性格特质的人，请从上述经历中提取3-5条最重要的记忆，并进行简短总结。

按重要性排序输出，每条总结使用一段简洁的文字（30-50字），确保包含相关的时间、地点、人物和事件。

输出格式: 每条记忆单独一行，不要编号，直接给出记忆内容。
"""
        
        # 使用LLM生成记忆总结
        summarized_memories = self.llm_engine.generate(prompt)
        
        # 如果生成失败，使用简化的提示重试
        if not summarized_memories or summarized_memories.strip() == "":
            simplified_prompt = f"请总结以下内容中最重要的3-5个要点，每点一行:\n\n{memories_text}"
            summarized_memories = self.llm_engine.generate(simplified_prompt)
            
            # 如果再次失败，保留1-2条原始记忆作为备选
            if not summarized_memories or summarized_memories.strip() == "":
                if len(self.short_term_memory) > 2:
                    summarized_memories = "\n".join(self.short_term_memory[-2:])
                else:
                    summarized_memories = "\n".join(self.short_term_memory)
        
        # 将总结的记忆分割成单独的条目
        important_memories = [m.strip() for m in summarized_memories.split("\n") if m.strip()]
        
        # 将重要记忆添加到长期记忆中
        for memory in important_memories:
            self._save_to_long_memory(memory)
            
        # 重新加载记忆以更新内存中的列表
        self._load_memories()
            
        # 检查并管理长期记忆容量
        self._manage_long_term_memory()
            
        # 检查短期记忆是否超过最大长度，如果超过，则删除最早的记忆直到剩余一半
        if len(self.short_term_memory) > self.max_short_term_memories:
            # 计算需要保留的数量（一半的最大容量）
            keep_count = self.max_short_term_memories // 2
            
            # 保留最新的记忆
            self.short_term_memory = self.short_term_memory[-keep_count:]
            
            # 更新短期记忆文件
            with open(self.shortterm_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.short_term_memory))
                
            print(f"{self.name} 的短期记忆超过最大限制，保留了最新的{keep_count}条记忆")
            
        # 更新向量存储
        self._update_vector_store()
        
        # 重置一天结束的状态
        self.status = "休息中"  # 睡眠时的状态
        
    def _reflect_on_daily_plan(self) -> str:
        """反思当天计划完成情况
        
        基于智能体的性格和背景，反思一天的计划完成度、成功之处和需要改进的地方
        
        Returns:
            str: 反思结果
        """
        if not self.daily_plan:
            return ""
            
        # 计算计划完成度
        total_plans = len(self.daily_plan)
        completed_plans = 0
        partially_completed_plans = 0
        locations_visited = set()
        completed_activities = []
        uncompleted_activities = []
        
        for i, plan in enumerate(self.daily_plan):
            # 获取已度过的轮数
            rounds_spent = plan.get("_rounds_spent", 0)
            
            # 如果完全完成了计划的时间
            if rounds_spent >= plan["duration"]:
                completed_plans += 1
                locations_visited.add(plan["location"])
                completed_activities.append(f"{i+1}. {plan['activity']} 在{plan['location']}")
            # 如果部分完成（至少度过了一轮）
            elif rounds_spent > 0:
                partially_completed_plans += 1
                locations_visited.add(plan["location"])
                completed_activities.append(f"{i+1}. 部分完成：{plan['activity']} 在{plan['location']} ({rounds_spent}/{plan['duration']}轮)")
            # 如果完全未完成
            else:
                uncompleted_activities.append(f"{i+1}. {plan['activity']} 在{plan['location']}")
        
        # 计算完成率
        completion_rate = int((completed_plans + 0.5 * partially_completed_plans) / total_plans * 100)
        
        # 构建提示
        prompt = f"""作为{self.name}，一个{self.background['gender']}性{self.background['age']}岁{self.background['occupation']}，MBTI性格类型为{self.mbti}，我需要对今天的计划完成情况进行反思。

今天的计划完成情况:
- 总计划数: {total_plans}
- 完全完成的计划: {completed_plans}
- 部分完成的计划: {partially_completed_plans}
- 未完成的计划: {total_plans - completed_plans - partially_completed_plans}
- 完成率: {completion_rate}%
- 访问的地点: {', '.join(locations_visited)}

完成的活动:
{chr(10).join(completed_activities)}

未完成的活动:
{chr(10).join(uncompleted_activities)}

请根据我的性格特点({self.mbti})和职业背景({self.background['occupation']})，写一段简短的日记式反思，包括：
1. 对今天计划完成情况的满意度
2. 哪些方面做得好，哪些方面需要改进
3. 对未完成计划的想法和明天可能的调整
4. 符合我{self.mbti}性格的情感和思考方式

请以第一人称撰写，保持自然流畅，30-80字左右。不要用"今天我..."开头，直接进入反思。
"""
        
        # 使用LLM生成反思
        reflection = self.llm_engine.generate(prompt)
        
        # 如果生成失败，使用简化的提示重试
        if not reflection or reflection.strip() == "":
            simplified_prompt = f"作为{self.name}，MBTI类型{self.mbti}，写一段简短反思，讨论今天完成了{completion_rate}%的计划，感受如何？"
            reflection = self.llm_engine.generate(simplified_prompt)
            
            # 如果再次失败，使用默认反思
            if not reflection or reflection.strip() == "":
                if completion_rate >= 70:
                    reflection = f"今天完成了大部分计划，很满意自己的效率。明天继续保持这种状态。"
                elif completion_rate >= 40:
                    reflection = f"今天完成了一些计划，但还有改进空间。明天需要更专注一些。"
                else:
                    reflection = f"今天计划完成得不太理想，明天需要重新调整时间分配和优先级。"
        
        # 在反思前添加引言
        return f"一天结束，我对今天的计划完成情况进行了反思：{reflection.strip()}"

    def plan(self, available_locations: List[str], location_descriptions: Dict[str, str], max_rounds: int = 5) -> List[Dict]:
        """制定每日计划
        
        根据智能体的背景、长期和短期记忆制定一天的活动计划
        
        Args:
            available_locations: 可用的位置列表
            location_descriptions: 位置描述字典 {位置名: 描述}
            max_rounds: 一天的最大轮数
            
        Returns:
            List[Dict]: 计划列表，每个元素是一个字典，包含位置、停留轮数、活动等信息
        """
        # 重置计划索引
        self.current_plan_index = 0
        
        # 获取最近的记忆，构建上下文
        recent_short_memories = self.short_term_memory[-min(10, len(self.short_term_memory)):]
        recent_short_memories_text = "\n".join(recent_short_memories)
        
        # 提取长期记忆中的关键信息
        key_long_memories = []
        for memory in self.long_term_memory[-20:]:  # 最近20条长期记忆
            for location in available_locations:
                if location in memory:
                    key_long_memories.append(memory)
                    break
        key_long_memories_text = "\n".join(key_long_memories[-5:])  # 最多5条与位置相关的长期记忆
        
        # 获取当前所在位置（从最新的短期记忆中提取）
        current_location = None
        for memory in reversed(self.short_term_memory):
            if "我现在在" in memory or "我从" in memory and "移动到了" in memory:
                for location in available_locations:
                    if f"我现在在{location}" in memory:
                        current_location = location
                        break
                    elif f"移动到了{location}" in memory:
                        current_location = location
                        break
                if current_location:
                    break
        
        # 如果无法确定当前位置，随机选择一个
        if not current_location and available_locations:
            current_location = random.choice(available_locations)
            
        # 构建位置描述文本
        locations_text = ""
        for loc in available_locations:
            desc = location_descriptions.get(loc, "")
            locations_text += f"- {loc}: {desc}\n"
            
        # 构建提示，用于生成计划
        prompt = f"""作为{self.name}，一个{self.background['gender']}性{self.background['age']}岁{self.background['occupation']}，MBTI性格类型为{self.mbti}，我需要根据我的背景和记忆制定今天的活动计划。

我的背景信息:
- 年龄: {self.background['age']}岁
- 性别: {self.background['gender']}
- 职业: {self.background['occupation']}
- 教育水平: {self.background['education']}
- 家乡: {self.background['hometown']}
- 外貌: {self.appearance}

我当前所在位置: {current_location}

可用的位置:
{locations_text}

我的近期记忆:
{recent_short_memories_text}

我的重要长期记忆:
{key_long_memories_text}

请根据以上信息，为我制定一个符合我性格特点和背景的一天计划，包括我要去的地点、在每个地点停留的时间和我要做的事情。

计划格式要求:
1. 分为{max_rounds}个时间段（上午、中午、下午、晚上等）
2. 每个时间段指定一个地点（从可用位置中选择）
3. 每个时间段1-2句话描述我计划做的事情
4. 行动计划要符合我的MBTI性格和职业背景
5. 考虑我的近期记忆中的活动和人际互动
6. 如果我最近与某人有互动，可以考虑安排与他们再次见面

请直接输出JSON格式，格式如下:
[
  {{
    "location": "地点名称",
    "duration": 1,
    "activity": "计划做的事情",
    "status": "状态描述（如'工作中'、'放松中'、'用餐中'等）"
  }},
  ...
]

确保输出是有效的JSON格式，并且每个地点都是从可用位置列表中选择的。每个时间段的duration总和应该是{max_rounds}。
"""
        
        # 使用LLM生成计划
        plan_text = self.llm_engine.generate(prompt)
        
        # 尝试解析生成的JSON
        try:
            # 提取JSON部分（可能有其他文本）
            json_start = plan_text.find('[')
            json_end = plan_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                plan_json = plan_text[json_start:json_end]
                daily_plan = json.loads(plan_json)
                
                # 验证并清理计划
                cleaned_plan = []
                total_duration = 0
                
                for item in daily_plan:
                    # 确保必要的键存在
                    if "location" not in item or "duration" not in item or "activity" not in item:
                        continue
                        
                    # 确保位置是有效的
                    if item["location"] not in available_locations:
                        # 替换为当前位置或随机位置
                        item["location"] = current_location or random.choice(available_locations)
                    
                    # 确保duration是有效的
                    try:
                        item["duration"] = int(item["duration"])
                        if item["duration"] < 1:
                            item["duration"] = 1
                    except:
                        item["duration"] = 1
                    
                    # 如果没有状态，根据活动生成一个
                    if "status" not in item or not item["status"]:
                        activity = item["activity"].lower()
                        if "工作" in activity or "学习" in activity:
                            item["status"] = "工作中"
                        elif "吃" in activity or "喝" in activity or "餐" in activity:
                            item["status"] = "用餐中"
                        elif "休息" in activity or "放松" in activity:
                            item["status"] = "放松中"
                        elif "聊天" in activity or "交流" in activity or "讨论" in activity:
                            item["status"] = "社交中"
                        else:
                            item["status"] = "活动中"
                            
                    cleaned_plan.append(item)
                    total_duration += item["duration"]
                
                # 确保总duration不超过max_rounds
                if total_duration > max_rounds:
                    # 按比例缩减duration
                    factor = max_rounds / total_duration
                    for item in cleaned_plan:
                        item["duration"] = max(1, int(item["duration"] * factor))
                    
                    # 可能需要再次调整以确保总和正确
                    total_duration = sum(item["duration"] for item in cleaned_plan)
                    if total_duration < max_rounds:
                        # 给最后一个计划项增加剩余的轮数
                        cleaned_plan[-1]["duration"] += (max_rounds - total_duration)
                    elif total_duration > max_rounds:
                        # 从最后一个计划项减去多余的轮数
                        extra = total_duration - max_rounds
                        for i in reversed(range(len(cleaned_plan))):
                            if cleaned_plan[i]["duration"] > extra:
                                cleaned_plan[i]["duration"] -= extra
                                break
                            else:
                                extra -= (cleaned_plan[i]["duration"] - 1)
                                cleaned_plan[i]["duration"] = 1
                                if extra == 0:
                                    break
                
                # 更新智能体的计划和状态
                self.daily_plan = cleaned_plan
                if cleaned_plan:
                    self.status = cleaned_plan[0]["status"]
                    
                # 记录计划到短期记忆
                plan_summary = "我的今日计划:\n"
                for i, item in enumerate(cleaned_plan):
                    plan_summary += f"{i+1}. 在{item['location']}停留{item['duration']}个时段，{item['activity']}。\n"
                self.add_memory(plan_summary)
                
                return cleaned_plan
            
        except Exception as e:
            print(f"{self.name}制定计划时出错: {e}")
            
        # 如果解析失败，创建一个简单的默认计划
        default_plan = []
        remaining_rounds = max_rounds
        
        # 当前位置停留1轮
        if current_location:
            default_plan.append({
                "location": current_location,
                "duration": 1,
                "activity": "查看周围环境，考虑接下来要做什么",
                "status": "观察中"
            })
            remaining_rounds -= 1
        
        # 随机选择其他位置
        while remaining_rounds > 0:
            # 排除当前位置和已经计划要去的位置
            planned_locations = [item["location"] for item in default_plan]
            available = [loc for loc in available_locations if loc not in planned_locations]
            
            # 如果没有更多可用位置，随机选择任意位置
            if not available:
                available = available_locations
                
            location = random.choice(available)
            duration = min(remaining_rounds, random.randint(1, 2))
            
            default_plan.append({
                "location": location,
                "duration": duration,
                "activity": f"前往{location}探索",
                "status": "探索中"
            })
            
            remaining_rounds -= duration
        
        # 更新智能体的计划和状态
        self.daily_plan = default_plan
        if default_plan:
            self.status = default_plan[0]["status"]
            
        # 记录计划到短期记忆
        plan_summary = "我制定了简单的今日计划:\n"
        for i, item in enumerate(default_plan):
            plan_summary += f"{i+1}. 在{item['location']}停留{item['duration']}个时段，{item['activity']}。\n"
        self.add_memory(plan_summary)
        
        return default_plan
        
    def get_next_planned_location(self) -> Optional[str]:
        """获取下一个计划中的位置
        
        根据当前计划索引返回下一个应该去的位置
        
        Returns:
            Optional[str]: 下一个计划位置，如果没有计划则返回None
        """
        if not self.daily_plan or self.current_plan_index >= len(self.daily_plan):
            return None
            
        next_location = self.daily_plan[self.current_plan_index]["location"]
        self.status = self.daily_plan[self.current_plan_index]["status"]
        return next_location
        
    def update_plan_progress(self) -> None:
        """更新计划进度
        
        每轮结束后调用，更新当前计划的进度
        """
        if not self.daily_plan:
            return
            
        # 如果当前计划已经完成所有时间段，移动到下一个计划
        if self.current_plan_index < len(self.daily_plan):
            current_plan = self.daily_plan[self.current_plan_index]
            current_plan["_rounds_spent"] = current_plan.get("_rounds_spent", 0) + 1
            
            # 如果已经完成当前计划的所有轮数，移动到下一个计划
            if current_plan["_rounds_spent"] >= current_plan["duration"]:
                self.current_plan_index += 1
                
                # 如果还有下一个计划，更新状态
                if self.current_plan_index < len(self.daily_plan):
                    self.status = self.daily_plan[self.current_plan_index]["status"]
                else:
                    self.status = "休息中" 

    def _generate_wealth(self) -> Dict[str, float]:
        """根据智能体的背景和性格，使用LLM生成初始财富值
        
        Returns:
            Dict[str, float]: 包含五种财富的字典：时间、社交、健康、精神和金钱
        """
        # 构建提示，基于智能体的属性
        prompt = f"""
作为一位角色财富状态生成器，请为以下角色生成初始财富状态。

角色信息:
- 姓名: {self.name}
- 性别: {self.background['gender']}
- 年龄: {self.background['age']}岁
- 职业: {self.background['occupation']}
- 教育程度: {self.background['education']}
- 家乡: {self.background['hometown']}
- MBTI性格: {self.mbti}
- 外貌: {self.appearance}

请生成五种财富的数值：
1. 时间财富: -1.0到1.0之间的浮点数，表示角色拥有的自由时间多少
   -1.0表示极度匮乏（非常忙碌），0表示平衡，1.0表示极度充裕（有大量闲暇时间）
2. 社交财富: -1.0到1.0之间的浮点数，表示角色的社交资源和能力
   -1.0表示极度匮乏（社交孤立），0表示一般，1.0表示极度丰富（社交资源丰富）
3. 健康财富: -1.0到1.0之间的浮点数，表示角色的身体健康状况
   -1.0表示极度不健康，0表示一般健康，1.0表示极度健康（体魄强健）
4. 精神财富: -1.0到1.0之间的浮点数，表示角色的精神状态和幸福感
   -1.0表示极度匮乏（精神压力大），0表示一般，1.0表示极度丰富（精神愉悦充实）
5. 金钱财富: 一个非负浮点数，基础为10000.0，表示角色拥有的金钱数量（单位：元）
   - 学生一般在5000-15000之间
   - 普通职业者一般在10000-50000之间
   - 高收入职业者一般在50000-200000之间
   - 要考虑年龄、职业、教育程度等因素

要求:
1. 请根据角色的背景、年龄、职业、性格特点逻辑推断合理的财富值
2. 所有值必须在规定范围内，且符合角色设定
3. 只返回JSON格式的财富数据，不要包含任何解释或其他文字

返回格式示例:
{{
  "time": 0.2,
  "social": -0.5,
  "health": 0.7,
  "mental": 0.1,
  "money": 25000.0
}}
"""
        
        try:
            # 获取LLM生成的财富数据
            response = self.llm_engine.generate(prompt)
            
            # 确保response不为None
            if not response or not response.strip():
                return self._generate_default_wealth()
                
            # 解析JSON
            try:
                wealth = json.loads(response)
                # 验证数据格式
                if all(key in wealth for key in ["time", "social", "health", "mental", "money"]):
                    # 验证数值范围
                    time_value = max(min(float(wealth["time"]), 1.0), -1.0)
                    social_value = max(min(float(wealth["social"]), 1.0), -1.0)
                    health_value = max(min(float(wealth["health"]), 1.0), -1.0)
                    mental_value = max(min(float(wealth["mental"]), 1.0), -1.0)
                    money_value = max(float(wealth["money"]), 0.0)
                    
                    return {
                        "time": time_value,
                        "social": social_value,
                        "health": health_value,
                        "mental": mental_value,
                        "money": money_value
                    }
            except:
                pass
                
            # 如果解析失败，使用默认值
            return self._generate_default_wealth()
                
        except Exception as e:
            print(f"生成财富数据时出错: {e}")
            return self._generate_default_wealth()
    
    def _generate_default_wealth(self) -> Dict[str, float]:
        """生成默认的财富数据，当LLM生成失败时使用"""
        # 基于职业和年龄设置默认金钱财富
        occupation = self.background["occupation"]
        age = self.background["age"]
        
        # 根据职业设置基础金钱
        if occupation == "学生":
            base_money = 8000.0
        elif occupation in ["工程师", "医生"]:
            base_money = 30000.0
        elif occupation == "教师":
            base_money = 20000.0
        elif occupation == "艺术家":
            base_money = 15000.0
        else:
            base_money = 10000.0
            
        # 根据年龄调整金钱（25岁以上每增加5岁增加20%）
        if age > 25:
            age_factor = 1.0 + ((age - 25) // 5) * 0.2
            money = base_money * age_factor
        else:
            money = base_money
            
        # 随机生成其他财富值
        return {
            "time": round(random.uniform(-0.7, 0.7), 2),
            "social": round(random.uniform(-0.7, 0.7), 2),
            "health": round(random.uniform(-0.3, 0.8), 2),
            "mental": round(random.uniform(-0.5, 0.8), 2),
            "money": round(money, 2)
        } 