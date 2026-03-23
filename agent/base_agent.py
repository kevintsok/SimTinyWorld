import os
import uuid
import json
import time
import random
from typing import List, Dict, Optional, Any, Sequence, Tuple
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.embeddings import Embeddings
from llm_engine.factory import LLMEngineFactory
from llm_engine.engine_verifier import EngineVerifier
from simulation.base import BaseAgent as SimBaseAgent
from simulation.base import EntityState

MAX_SHORT_TERM_MEM = 50  # 短期记忆条目上限
MAX_LONG_TERM_MEM = 200   # 长期记忆条目上限

class Memory(BaseModel):
    content: str
    timestamp: float
    importance: float

class LLMEngineEmbeddings(Embeddings):
    """将LLM引擎的嵌入功能包装为LangChain Embeddings对象"""
    
    def __init__(self, llm_engine):
        # 确保llm_engine不是字符串
        from llm_engine.factory import LLMEngineFactory
        if isinstance(llm_engine, str):
            llm_engine = LLMEngineFactory.create_engine(llm_engine)
        self.llm_engine = llm_engine
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """对多个文本进行嵌入"""
        # 确保llm_engine不是字符串
        from llm_engine.factory import LLMEngineFactory
        engine = self.llm_engine
        if isinstance(engine, str):
            engine = LLMEngineFactory.create_engine(engine)
        if engine is None:
            # 返回随机嵌入向量作为后备
            import random
            dim = 384  # 标准嵌入维度
            return [[random.random() for _ in range(dim)] for _ in texts]
        return engine.get_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """对单个查询文本进行嵌入"""
        # 确保llm_engine不是字符串
        from llm_engine.factory import LLMEngineFactory
        engine = self.llm_engine
        if isinstance(engine, str):
            engine = LLMEngineFactory.create_engine(engine)
        if engine is None:
            # 返回随机嵌入向量作为后备
            import random
            dim = 384  # 标准嵌入维度
            return [random.random() for _ in range(dim)]
        return engine.get_embeddings(text)

class BaseAgent(SimBaseAgent):
    def __init__(self, id=None, name=None, gender=None, age=None, mbti=None,
                 background=None, appearance=None, vector_store_dir=None,
                 init_wealth=None, engine=None):
        """初始化智能体

        Args:
            id: 智能体ID
            name: 智能体名称
            gender: 性别
            age: 年龄
            mbti: MBTI人格
            background: 背景故事
            appearance: 外貌描述
            vector_store_dir: 向量存储目录
            init_wealth: 初始财富
            engine: LLM引擎
        """
        super().__init__(id or str(uuid.uuid4()), name or "Unknown")

        self.gender = gender
        self.age = age
        self.mbti = mbti
        self.background = background
        self.appearance = appearance

        self.ultimate_goal = "繁衍"

        self.status = "空闲"
        self.current_plan = None
        self.daily_plan = []
        self.current_plan_index = 0

        from llm_engine.factory import has_global_engine, get_global_engine
        if engine:
            self.llm_engine = engine
        elif has_global_engine():
            self.llm_engine = get_global_engine()
        else:
            self.llm_engine = EngineVerifier().get_first_available_engine()
        
        if init_wealth:
            self.wealth = init_wealth
        else:
            if self.background and self.appearance and self.name and self.mbti:
                try:
                    self.wealth = self._generate_default_wealth()
                    dynamic_wealth = self._generate_wealth()
                    if dynamic_wealth:
                        self.wealth = dynamic_wealth
                except Exception as e:
                    print(f"生成财富时出错: {e}，使用随机默认财富")
                    self.wealth = self._generate_default_wealth()
            else:
                self.wealth = self._generate_default_wealth()

        self.mood = self._generate_initial_mood()
        self._init_memory_storage(vector_store_dir)

        if not self.long_term_memory:
            if self.llm_engine and hasattr(self.llm_engine, 'mock_mode') and not self.llm_engine.mock_mode:
                self._generate_initial_long_term_memories()
            else:
                # LLM不可用（mock模式），生成基础记忆
                self._generate_basic_memories()

    def _generate_initial_mood(self):
        """根据MBTI和背景生成初始心情"""
        # 默认心情值
        mood_value = 0.0
        
        # 根据MBTI调整基础心情
        if self.mbti:
            # 外向型(E)的人初始心情略偏正面
            if self.mbti.startswith('E'):
                mood_value += 0.2
            # 内向型(I)的初始心情略偏中性
            else:
                mood_value -= 0.1
                
            # 思考型(T)的人情绪波动较小
            if 'T' in self.mbti:
                mood_value *= 0.9
            # 情感型(F)的人情绪波动较大
            else:
                mood_value *= 1.1
                
            # 判断型(J)的人喜欢确定性，初始心情略偏正面
            if self.mbti.endswith('J'):
                mood_value += 0.1
            # 感知型(P)的人喜欢灵活性，不确定性可能导致轻微焦虑
            else:
                mood_value -= 0.1
        
        # 确保心情值在-1.0到1.0之间
        mood_value = max(-1.0, min(1.0, mood_value))
        
        # 根据背景调整心情
        if self.background and random.random() < 0.3:  # 30%概率根据背景调整
            # 简单检测背景中的积极词汇
            positive_words = ["成功", "幸福", "快乐", "成就", "喜欢", "热爱", "满意"]
            negative_words = ["失败", "挫折", "痛苦", "困难", "压力", "焦虑", "不满"]
            
            for word in positive_words:
                if word in self.background:
                    mood_value += 0.05  # 每个积极词汇略微提升心情
                    
            for word in negative_words:
                if word in self.background:
                    mood_value -= 0.05  # 每个消极词汇略微降低心情
            
            # 再次确保心情值在范围内
            mood_value = max(-1.0, min(1.0, mood_value))
        
        # 添加随机波动
        mood_value += random.uniform(-0.1, 0.1)
        mood_value = max(-1.0, min(1.0, mood_value))
        
        # 构建心情对象
        mood = {
            "value": round(mood_value, 2),
            "description": self._get_mood_description(mood_value),
            "last_update": time.time()
        }
        
        return mood
    
    @staticmethod
    def _get_mood_description(mood_value):
        """根据心情值获取对应的描述"""
        if mood_value < -0.8:
            return "沮丧"
        elif mood_value < -0.6:
            return "难过"
        elif mood_value < -0.3:
            return "不悦"
        elif mood_value < -0.1:
            return "有点低落"
        elif mood_value < 0.1:
            return "平静"
        elif mood_value < 0.3:
            return "还不错"
        elif mood_value < 0.6:
            return "愉快"
        elif mood_value < 0.8:
            return "开心"
        else:
            return "兴奋"
            
    def update_mood(self, event_type, intensity, reason=None):
        """更新智能体的心情
        
        Args:
            event_type: 事件类型，如'social', 'work', 'rest'等
            intensity: 事件的强度，正值表示积极事件，负值表示消极事件
            reason: 心情变化的原因描述
        """
        # 获取当前心情值
        current_mood = self.mood["value"]
        
        # 根据MBTI特性调整心情变化幅度
        adjusted_intensity = intensity
        
        if self.mbti:
            # 思考型(T)的人情绪波动较小
            if 'T' in self.mbti:
                adjusted_intensity *= 0.7
            # 情感型(F)的人情绪波动较大
            elif 'F' in self.mbti:
                adjusted_intensity *= 1.3
                
            # 外向型(E)和内向型(I)对社交事件的反应不同
            if event_type in ['social', 'conversation', 'meeting']:
                if self.mbti.startswith('E'):
                    if adjusted_intensity > 0:
                        adjusted_intensity *= 1.2  # 外向型从社交中获得更多能量
                    else:
                        adjusted_intensity *= 0.8  # 外向型受社交挫折影响较小
                else:  # 内向型
                    if adjusted_intensity > 0:
                        adjusted_intensity *= 0.8  # 内向型从社交中获得能量较少
                    else:
                        adjusted_intensity *= 1.2  # 内向型受社交挫折影响较大
        
        # 计算新的心情值
        new_mood = current_mood + adjusted_intensity
        
        # 确保心情值在-1.0到1.0之间
        new_mood = max(-1.0, min(1.0, new_mood))
        
        # 记录显著的心情变化到记忆中
        if abs(new_mood - current_mood) > 0.1:
            change_type = "提升" if new_mood > current_mood else "降低"
            memory_text = f"我的心情{change_type}了" + (f"，因为{reason}" if reason else "")
            self.add_memory(memory_text)
        
        # 更新心情
        self.mood = {
            "value": round(new_mood, 2),
            "description": self._get_mood_description(new_mood),
            "last_update": time.time()
        }
        
        return self.mood
    
    def response(self, query, system_prompt=None, history=None):
        """根据查询生成回复
        
        Args:
            query: 查询文本
            system_prompt: 系统提示
            history: 对话历史

        Returns:
            str: 生成的回复
        """
        try:
            # 获取LLM引擎（提前检查，避免后续昂贵操作）
            llm_engine = self._get_llm_engine()
            if llm_engine is None:
                return "（沉默不语）"

            # 获取相关的记忆
            relevant_docs, short_term_memory = self._get_relevant_memory(query)
            
            # 构建提示
            # 基础身份信息
            identity = (
                f"我是{self.name}，{self.age}岁，{self.gender}性。"
                f"我的MBTI是{self.mbti}。"
                f"我的外貌：{self.appearance}"
                f"我的当前状态是：{self.status}"
                f"我的当前心情是：{self.mood['description']}"
            )
            
            # 生成系统提示
            if not system_prompt:
                system_prompt = (
                    f"你将模拟一个名为{self.name}的人物，根据以下信息生成对话回复。\n\n"
                    f"## 你的身份\n{identity}\n\n"
                    f"## 你的背景\n{self.background}\n\n"
                    f"## 你的MBTI解析\n{self._get_mbti_traits()}\n\n"
                    f"## 你的记忆\n{short_term_memory}\n\n"
                    f"## 你的心情\n现在你感到{self.mood['description']}(心情值:{self.mood['value']})。让这种情绪适当地影响你的回复风格。\n\n"
                    f"根据你的记忆和个性特征，生成一个真实、自然、符合你性格和当前心情的回复。"
                    f"回复应该反映你的MBTI特征和心情状态。"
                    f'直接以第一人称回复，不要说"作为[角色名]"或"我会说"这样的前缀。'
                    f"回复应该是流畅的中文，符合日常对话的语气和风格。"
                )

            # 如果有对话历史，添加到system_prompt
            if history and len(history) > 0:
                history_text = "\n".join([f"{h['speaker']}: {h['content']}" for h in history])
                system_prompt += f"\n\n## 最近对话历史\n{history_text}\n\n请结合对话历史，保持话题连贯性，以自然的方式继续对话。"

            # 添加对话自然度指导
            system_prompt += """
## 对话风格要求
- 真实的日常对话应该有自然的打断、重申、疑问
- 不要每句话都太长或太正式
- 可以使用口语化表达，如"嗯"、"其实"、"怎么说呢"、"这个嘛"
- 对话应该像真实的人际交流，有起承转合
- 可以反问、追问、表达疑惑
"""

            # 根据MBTI和心情调整回复风格
            mbti_mood_prompt = self._get_response_style_by_mood()
            if mbti_mood_prompt:
                system_prompt += f"\n\n{mbti_mood_prompt}"
                
            # 获取LLM回复
            if hasattr(llm_engine, 'generate_response'):
                response = llm_engine.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=query,
                    max_tokens=200,
                    temperature=0.7
                )
            else:
                # 如果不支持generate_response方法，使用generate方法
                combined_prompt = f"{system_prompt}\n\n用户: {query}\n\n回复:"
                response = llm_engine.generate(combined_prompt)
            
            # 根据心情和MBTI特性调整回复长度
            if response:
                # 激动的心情可能导致回复变长
                if self.mood['value'] > 0.7:
                    # 保持原来的长度或略微增加
                    pass
                # 不好的心情可能导致回复变短
                elif self.mood['value'] < -0.5:
                    words = response.split()
                    if len(words) > 10:
                        # 减少回复长度，但保持至少5个词
                        reduced_length = max(5, int(len(words) * 0.7))
                        response = " ".join(words[:reduced_length]) + "..."
            
            return response
            
        except Exception as e:
            print(f"生成回复时出错: {e}")
            return f""
    
    def _get_response_style_by_mood(self):
        """根据MBTI和当前心情生成回复风格指导"""
        mood_value = self.mood["value"]
        mood_desc = self.mood["description"]
        
        # 基于心情的基础风格
        style_prompt = f"由于你现在感到{mood_desc}，"
        
        # 根据心情值确定回复风格
        if mood_value < -0.6:  # 非常负面的心情
            style_prompt += "你的回复应该反映出低落的情绪，语速较慢，句子较短，可能不愿多谈。"
        elif mood_value < -0.2:  # 略微负面的心情
            style_prompt += "你的回复应该显得有些疲惫或不耐烦，但仍然保持基本礼貌。"
        elif mood_value < 0.2:  # 中性心情
            style_prompt += "你的回复应该平静、理性，不带太多情绪色彩。"
        elif mood_value < 0.6:  # 略微正面的心情
            style_prompt += "你的回复应该友好、活跃，愿意交流。"
        else:  # 非常正面的心情
            style_prompt += "你的回复应该充满热情和能量，可能会使用更多感叹词和积极词汇。"
        
        # 根据MBTI添加个性化风格
        if self.mbti:
            style_prompt += "\n\n此外，基于你的MBTI："
            
            # 内向(I)/外向(E)
            if self.mbti.startswith('I'):
                style_prompt += "\n- 作为内向型人格，你的回复通常更加深思熟虑，可能会先观察情况再发言。"
            else:
                style_prompt += "\n- 作为外向型人格，你的回复通常更加直接，喜欢分享想法和引导对话。"
            
            # 感觉(S)/直觉(N)
            if 'S' in self.mbti:
                style_prompt += "\n- 你更关注具体事实和细节，喜欢谈论现实和实际经验。"
            else:
                style_prompt += "\n- 你更关注概念和可能性，喜欢谈论未来和理论观点。"
            
            # 思考(T)/情感(F)
            if 'T' in self.mbti:
                style_prompt += "\n- 你的回复倾向于逻辑和客观，较少表达情感。"
            else:
                style_prompt += "\n- 你的回复倾向于表达情感和关心他人，注重和谐。"
            
            # 判断(J)/感知(P)
            if self.mbti.endswith('J'):
                style_prompt += "\n- 你喜欢计划和确定性，回复可能会包含决定和结论。"
            else:
                style_prompt += "\n- 你喜欢保持灵活性和选择开放，回复可能会保留多种可能性。"

        return style_prompt

    def should_conversation_end(self, conversation_history: List[Dict]) -> bool:
        """判断对话是否应该结束

        Args:
            conversation_history: 对话历史列表 [{"speaker": "张三", "content": "你好"}]

        Returns:
            bool: 对话是否应该结束
        """
        if len(conversation_history) < 2:
            return False

        try:
            # 最近3轮对话
            recent = conversation_history[-3:]
            history_text = "\n".join([f"{h['speaker']}：{h['content']}" for h in recent])

            prompt = f"""判断以下对话是否已经自然结束：

{history_text}

如果对话中的话题已经得到充分讨论，或者双方已经说再见/告别语，回答"是"。
如果对话仍在进行中或有继续讨论的空间，回答"否"。

回答格式：只需要回答"是"或"否"。"""

            llm_engine = self._get_llm_engine()
            if hasattr(llm_engine, 'generate'):
                response = llm_engine.generate(prompt)
            else:
                response = ""

            return "是" in response

        except Exception as e:
            print(f"判断对话结束出错: {e}")
            return False

    def sleep(self):
        """智能体睡眠，恢复部分属性，评估睡眠质量"""
        # 获取今天短期记忆和当前心情，用于评估睡眠质量
        recent_memories = "\n".join(self.short_term_memory[-min(10, len(self.short_term_memory)):])
        current_mood = self.mood["value"]
        mood_desc = self.mood["description"]
        
        # 使用LLM评估睡眠质量
        sleep_quality = self._evaluate_sleep_quality(recent_memories, current_mood, mood_desc)
        
        # 记录睡眠和质量
        quality_desc = sleep_quality["description"]
        quality_score = sleep_quality["score"]
        self.add_memory(f"我睡了一晚上觉，睡眠质量{quality_desc}。{sleep_quality['reason']}")
        
        # 更新状态
        self.status = "刚醒来"
        
        # 基于睡眠质量调整健康和心理财富值
        for wealth_type in ["health", "mental"]:
            current = self.wealth.get(wealth_type, 0)
            
            # 基础恢复值
            if current < 0:
                # 如果当前为负，基础恢复较多
                base_change = random.uniform(0.08, 0.15)
            else:
                # 如果当前为正，基础恢复较少
                base_change = random.uniform(0.03, 0.08)
            
            # 睡眠质量调整因子
            # 质量越高，恢复越多；质量不佳，恢复减少
            quality_factor = (quality_score - 3) / 10  # -0.2 到 +0.2 的调整
            
            # 最终变化值
            change = base_change + quality_factor
            
            # 健康受睡眠质量影响较大
            if wealth_type == "health":
                change *= 1.2
                
            # 确保变化在合理范围内
            change = max(0, change)  # 确保睡眠至少不会减少健康和心理状态
            
            # 应用变化
            new_value = min(current + change, 1.0)
            self.wealth[wealth_type] = round(new_value, 2)
        
        # 基于睡眠质量调整心情
        # 优质睡眠会显著改善心情，糟糕睡眠对心情影响有限
        
        # 基础心情调整
        if current_mood < 0:
            # 负面心情的基础改善
            base_mood_change = random.uniform(0.05, 0.2)
        elif current_mood > 0.5:
            # 过于兴奋的心情会平静
            base_mood_change = -random.uniform(0.05, 0.15)
        else:
            # 中性心情小幅波动
            base_mood_change = random.uniform(-0.1, 0.1)
        
        # 睡眠质量对心情的额外影响
        quality_mood_factor = (quality_score - 3) / 5  # -0.4 到 +0.4 的调整
        
        # 最终心情变化
        mood_change = base_mood_change + quality_mood_factor
        
        # 应用心情变化
        new_mood = current_mood + mood_change
        # 确保心情在合理范围内
        new_mood = max(min(new_mood, 1.0), -1.0)
        
        # 更新心情
        self.mood = {
            "value": round(new_mood, 2),
            "description": self._get_mood_description(new_mood),
            "last_update": time.time()
        }
        
        # 清空短期记忆并总结为长期记忆
        self._summarize_and_clear_short_term_memory()
        
        return f"睡眠完成，睡眠质量{quality_desc}，状态已恢复"
        
    def _evaluate_sleep_quality(self, recent_memories: str, mood_value: float, mood_description: str) -> Dict:
        """评估睡眠质量
        
        基于当天的活动、心情状态和MBTI性格特征评估睡眠质量
        
        Args:
            recent_memories: 最近的记忆内容
            mood_value: 当前的心情值
            mood_description: 当前的心情描述
            
        Returns:
            Dict: 包含睡眠质量评分(1-5)、描述和原因的字典
        """
        # 构建提示
        prompt = f"""作为睡眠质量评估专家，请为{self.name}评估今晚的睡眠质量。

个人信息:
- 姓名: {self.name}
- 性别: {self.gender}
- 年龄: {self.age}
- 职业: {self.background.get('occupation', '未知')}
- MBTI性格: {self.mbti}
- 当前心情: {mood_description} (值: {mood_value})

今天的经历:
{recent_memories}

请考虑以下因素评估睡眠质量:
1. 当天的活动强度和类型
2. 心理和情绪状态
3. MBTI人格特质与睡眠的关系
4. 当天的社交互动情况
5. 可能的压力源或放松活动

请提供:
1. 睡眠质量评分(1-5分，1分=很差，2分=较差，3分=一般，4分=良好，5分=非常好)
2. 简短的睡眠质量描述词(如"良好"、"一般"、"糟糕"等)
3. 睡眠质量评估的原因(1-2句话)

要求:
- 基于提供的信息进行合理推断
- 考虑MBTI性格与睡眠的相关性
- 只返回JSON格式，不要有其他解释

返回格式示例:
{{
  "score": 4,
  "description": "良好",
  "reason": "今天活动适度，心情稳定，没有明显压力源"
}}
"""
        
        try:
            # 获取LLM生成的睡眠质量评估
            response = self._generate_with_llm(prompt)
            
            # 确保response不为None
            if not response or not response.strip():
                return self._get_default_sleep_quality()
                
            # 尝试从响应中提取JSON部分
            sleep_quality = self._extract_json_from_response(response)
            if sleep_quality and all(key in sleep_quality for key in ["score", "description", "reason"]):
                # 确保分数在1-5范围内
                score = max(min(int(sleep_quality["score"]), 5), 1)
                return {
                    "score": score,
                    "description": sleep_quality["description"],
                    "reason": sleep_quality["reason"]
                }

            # 如果解析失败，使用默认值
            return self._get_default_sleep_quality()
                
        except Exception as e:
            print(f"评估睡眠质量时出错: {e}")
            return self._get_default_sleep_quality()
            
    def _get_default_sleep_quality(self) -> Dict:
        """获取默认的睡眠质量评估
        
        当LLM评估失败时使用基于当前状态的简单规则生成睡眠质量
        
        Returns:
            Dict: 包含睡眠质量评分、描述和原因的字典
        """
        # 基于当前心情生成睡眠质量
        mood_value = self.mood["value"]
        
        if mood_value < -0.5:
            # 心情很差，睡眠质量较低
            score = random.randint(1, 2)
            descriptions = ["很差", "糟糕", "不安"]
            reasons = ["心情低落，辗转反侧难以入睡", "负面情绪导致多次惊醒", "睡眠浅且不连贯"]
        elif mood_value < 0:
            # 心情略差，睡眠质量偏低
            score = random.randint(2, 3)
            descriptions = ["一般", "尚可", "较差"]
            reasons = ["情绪有些波动，影响了入睡", "睡眠较轻，偶有醒来", "没有得到充分的休息"]
        elif mood_value < 0.5:
            # 心情中性，睡眠质量中等
            score = 3
            descriptions = ["一般", "普通", "还算可以"]
            reasons = ["入睡正常，睡眠质量一般", "有做梦但不影响休息", "得到了基本的休息"]
        elif mood_value < 0.8:
            # 心情良好，睡眠质量不错
            score = 4
            descriptions = ["良好", "不错", "舒适"]
            reasons = ["心情放松，睡眠连贯", "睡眠深沉，醒来精神好", "得到了充分的休息"]
        else:
            # 心情很好，睡眠质量极佳
            score = 5
            descriptions = ["非常好", "极佳", "完美"]
            reasons = ["完全放松，一夜好眠", "深度睡眠，醒来神清气爽", "睡眠质量极佳，精力充沛"]
        
        return {
            "score": score,
            "description": random.choice(descriptions),
            "reason": random.choice(reasons)
        }

    def _summarize_and_clear_short_term_memory(self):
        """总结短期记忆中的重要内容，将其保存到长期记忆中，并清理短期记忆
        
        此方法在智能体睡眠时调用，它会分析短期记忆中的内容，提取重要信息，
        将这些信息存入长期记忆，并清空或减少短期记忆的数量。
        """
        # 如果没有短期记忆，直接返回
        if not self.short_term_memory:
            return
            
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
6. 与我的终极目标({self.ultimate_goal})相关的进展

对于你({self.name})这样一个{self.gender or self.background.get('gender', '未知')}性、{self.age or self.background.get('age', 25)}岁{self.background.get('occupation', '未知职业')}，具有{self.mbti}性格特质的人，请从上述经历中提取3-5条最重要的记忆，并进行简短总结。

按重要性排序输出，每条总结使用一段简洁的文字（30-50字），确保包含相关的时间、地点、人物和事件。特别关注那些有助于实现终极目标({self.ultimate_goal})的经历。

输出格式: 每条记忆单独一行，不要编号，直接给出记忆内容。
"""
        
        # 使用LLM生成记忆总结
        summarized_memories = self._generate_with_llm(prompt)
        
        # 如果生成失败，使用简化的提示重试
        if not summarized_memories or summarized_memories.strip() == "":
            simplified_prompt = f"请总结以下内容中最重要的3-5个要点，每点一行:\n\n{memories_text}"
            summarized_memories = self._generate_with_llm(simplified_prompt)
            
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
            
        # 检查并管理长短期记忆容量
        self._manage_long_term_memory()
            
        self._manage_short_term_memory()
            
        # 更新向量存储
        self._update_vector_store()

    def to_dict(self):
        """将智能体转换为字典表示"""
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "mbti": self.mbti,
            "background": self.background,
            "appearance": self.appearance,
            "status": self.status,
            "current_plan": self.current_plan,
            "wealth": self.wealth,
            "mood": self.mood,
            "vector_store_dir": self.vector_store_dir,
            # 新增字段
            "short_term_memory": getattr(self, "short_term_memory", []),
            "long_term_memory": getattr(self, "long_term_memory", []),
            "daily_plan": getattr(self, "daily_plan", None),
            "current_plan_index": getattr(self, "current_plan_index", 0),
            "position": getattr(self, "position", None),
            "ultimate_goal": getattr(self, "ultimate_goal", "繁衍")
        }

    @classmethod
    def from_dict(cls, data, engine=None):
        """从字典创建智能体实例

        Args:
            data: 字典数据
            engine: LLM引擎（可选）

        Returns:
            BaseAgent: 恢复的智能体实例
        """
        # 先创建一个带有基本属性的实例
        agent = cls(
            id=data.get("id"),
            name=data.get("name"),
            gender=data.get("gender"),
            age=data.get("age"),
            mbti=data.get("mbti"),
            background=data.get("background"),
            appearance=data.get("appearance"),
            vector_store_dir=data.get("vector_store_dir"),
            engine=engine
        )

        # 单独处理财富，确保在背景和属性设置后生成财富
        if "wealth" in data and data["wealth"]:
            agent.wealth = data["wealth"]
        else:
            # 尝试生成个性化财富
            try:
                agent.wealth = agent._generate_default_wealth()  # 先生成默认财富
                if hasattr(agent, 'background') and agent.background and agent.appearance:
                    dynamic_wealth = agent._generate_wealth()  # 尝试生成动态财富
                    if dynamic_wealth:  # 如果生成成功，使用动态财富
                        agent.wealth = dynamic_wealth
            except Exception as e:
                print(f"从字典生成{agent.name}财富时出错: {e}，使用随机默认财富")
                agent.wealth = agent._generate_default_wealth()

        agent.status = data.get("status", "空闲")
        agent.current_plan = data.get("current_plan")

        # 恢复心情，如果字典中没有心情数据，则生成一个新的
        if "mood" in data:
            agent.mood = data["mood"]
        else:
            agent.mood = agent._generate_initial_mood()

        # 恢复新增字段
        agent.ultimate_goal = data.get("ultimate_goal", "繁衍")
        agent.position = data.get("position")

        # 恢复每日计划
        if "daily_plan" in data:
            agent.daily_plan = data["daily_plan"]
        if "current_plan_index" in data:
            agent.current_plan_index = data["current_plan_index"]

        # 恢复记忆并重建FAISS
        if "short_term_memory" in data:
            agent.short_term_memory = data["short_term_memory"]
            # 写入短期记忆文件
            if hasattr(agent, "shortterm_file") and agent.short_term_memory:
                with open(agent.shortterm_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(agent.short_term_memory))

        if "long_term_memory" in data:
            agent.long_term_memory = data["long_term_memory"]
            # 写入长期记忆文件
            if hasattr(agent, "longterm_file") and agent.long_term_memory:
                with open(agent.longterm_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(agent.long_term_memory))

        # 重建FAISS索引
        if hasattr(agent, "_update_vector_store"):
            agent._update_vector_store()

        return agent

    # ===== 继承自 SimBaseAgent 的抽象方法实现 =====

    def think(self, prompt: str, history: List[Dict] = None) -> str:
        """思考并生成回复

        Args:
            prompt: 输入提示词
            history: 可选的对话历史列表

        Returns:
            str: 生成的回复
        """
        return self.response(prompt, history=history)

    def perceive(self, event) -> None:
        """感知事件

        Args:
            event: 事件对象
        """
        # 将事件转换为记忆
        content = f"感知到事件: {event.event_type}"
        if event.data:
            content += f" - {json.dumps(event.data, ensure_ascii=False)}"
        self.add_memory(content)

    def act(self) -> Dict[str, Any]:
        """采取行动

        Returns:
            Dict[str, Any]: 行动结果
        """
        # 默认行动是保持当前状态
        return {
            "type": "idle",
            "status": self.status,
            "location": self.position
        }

    def update(self, delta_time: float) -> None:
        """更新实体状态

        Args:
            delta_time: 时间增量
        """
        # 简单的时间推进，更新位置等
        pass

    # ===== 原有方法 =====

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
        with open(self.shortterm_file, "a", encoding="utf-8") as f:
            f.write("\n" + content)
            
        # 更新内存中的短期记忆
        self.short_term_memory.append(content)
        
        # 管理短期记忆容量
        self._manage_short_term_memory()
    
    def _manage_short_term_memory(self):
        """管理短期记忆容量，确保不超过最大限制"""
        # 如果短期记忆超过最大限制，删除最早的记忆
        if len(self.short_term_memory) > MAX_SHORT_TERM_MEM:
            # 保留最新的记忆
            self.short_term_memory = self.short_term_memory[-MAX_SHORT_TERM_MEM:]
            
            # 更新短期记忆文件
            with open(self.shortterm_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.short_term_memory))
    
    def _manage_long_term_memory(self):
        """管理长期记忆容量，确保不超过最大限制"""
        # 如果长期记忆超过最大限制，删除最早的记忆
        if len(self.long_term_memory) > MAX_LONG_TERM_MEM:
            # 保留最新的记忆
            self.long_term_memory = self.long_term_memory[-MAX_LONG_TERM_MEM:]
            
            # 更新长期记忆文件
            with open(self.longterm_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.long_term_memory))
            
            # 更新向量存储
            self._update_vector_store()
            
    def _save_to_long_memory(self, content: str):
        """保存记忆到长期记忆文件，以纯文本格式"""
        with open(self.longterm_file, "a", encoding="utf-8") as f:
            f.write("\n" + content)
    
    def query_memory(self, query: str) -> str:
        """为兼容性保留的方法，重定向到response方法"""
        return self.response(query)

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
            "gender": self.gender,
            "age": self.age,
            "mbti": self.mbti,
            "background": self.background,
            "appearance": self.appearance,
            "wealth": self.wealth,
            "mood": self.mood,
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
        agent.gender = identity.get("gender")
        agent.age = identity.get("age")
        agent.mbti = identity["mbti"]
        agent.background = identity["background"]
        agent.long_term_memory = []
        agent.short_term_memory = []
        
        # 初始化LLM引擎 - 只初始化一次
        agent.llm_engine = LLMEngineFactory.create_engine(llm_kwargs.get("llm_engine_type", "qwen"), **llm_kwargs)
        
        # 加载外貌信息
        if "appearance" in identity:
            agent.appearance = identity["appearance"]
        else:
            agent.appearance = agent._generate_appearance()
            
        if "wealth" in identity:
            agent.wealth = identity["wealth"]
        else:
            agent.wealth = agent._generate_wealth()
        if "mood" in identity:
            agent.mood = identity["mood"]
            agent.mood_history = []  # 初始化心情历史
        else:
            agent.mood = agent._generate_initial_mood()
            agent.mood_history = []
        
        # 设置记忆目录和文件路径
        agent.memory_dir = f"{directory}/{agent_id}"
        agent.longterm_file = f"{agent.memory_dir}/long.txt"
        agent.shortterm_file = f"{agent.memory_dir}/short.txt"
        
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

    def _generate_wealth(self) -> Dict[str, float]:
        """根据智能体的背景和性格，使用LLM生成初始财富值
        
        Returns:
            Dict[str, float]: 包含五种财富的字典：时间、社交、健康、精神和金钱
        """
        # 如果缺少必要信息或背景信息不完整，使用默认值
        if not hasattr(self, 'background') or not self.background:
            return self._generate_default_wealth()
            
        # 构建提示，基于智能体的属性
        gender = self.gender or self.background.get('gender', '未知')
        age = self.age or self.background.get('age', 25)
        occupation = self.background.get('occupation', '未知职业')
        education = self.background.get('education', '未知')
        hometown = self.background.get('hometown', '未知')
        
        prompt = f"""
作为一位角色财富状态生成器，请为以下角色生成初始财富状态。

角色信息:
- 姓名: {self.name}
- 性别: {gender}
- 年龄: {age}岁
- 职业: {occupation}
- 教育程度: {education}
- 家乡: {hometown}
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
5. 金钱财富: 一个非负浮点数，表示角色拥有的金钱数量（单位：元）
   - 学生一般在5000-15000之间
   - 普通职业者一般在10000-50000之间
   - 高收入职业者一般在50000-200000之间
   - 要考虑年龄、职业、教育程度等因素

要求:
1. 请根据角色的背景、年龄、职业、性格特点逻辑推断合理的财富值
2. 所有值必须在规定范围内，且符合角色设定
3. 只返回JSON格式的财富数据，不要包含任何解释或其他文字
4. 确保数值有多样性，体现角色的独特性

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
            response = self._generate_with_llm(prompt)
            
            # 确保response不为None
            if not response or not response.strip():
                print(f"为{self.name}生成财富时LLM返回空响应")
                return self._generate_default_wealth()
                
            # 尝试从响应中提取JSON部分
            wealth = self._extract_json_from_response(response)
            if wealth and all(key in wealth for key in ["time", "social", "health", "mental", "money"]):
                # 验证数值范围
                time_value = max(min(float(wealth["time"]), 1.0), -1.0)
                social_value = max(min(float(wealth["social"]), 1.0), -1.0)
                health_value = max(min(float(wealth["health"]), 1.0), -1.0)
                mental_value = max(min(float(wealth["mental"]), 1.0), -1.0)
                money_value = max(float(wealth["money"]), 0.0)

                return {
                    "time": round(time_value, 2),
                    "social": round(social_value, 2),
                    "health": round(health_value, 2),
                    "mental": round(mental_value, 2),
                    "money": round(money_value, 2)
                }
            else:
                print(f"为{self.name}生成财富时JSON格式不完整: {wealth}")

            # 如果解析失败，使用默认值
            return self._generate_default_wealth()

        except Exception as e:
            print(f"为{self.name}生成财富数据时出错: {e}")
            return self._generate_default_wealth()
    
    @staticmethod
    def _derive_status_from_activity(activity: str) -> str:
        """根据活动内容推导状态字符串"""
        activity_lower = activity.lower()
        if "工作" in activity_lower or "学习" in activity_lower:
            return "工作中"
        elif "吃" in activity_lower or "喝" in activity_lower or "餐" in activity_lower:
            return "用餐中"
        elif "休息" in activity_lower or "放松" in activity_lower:
            return "放松中"
        elif "聊天" in activity_lower or "交流" in activity_lower or "讨论" in activity_lower:
            return "社交中"
        else:
            return "活动中"

    @staticmethod
    def _extract_json_from_response(response: str) -> Optional[Dict]:
        """从LLM响应中提取JSON对象"""
        if not response:
            return None
        response = response.strip()
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            try:
                return json.loads(response[start_idx:end_idx])
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _normalize_plan_durations(plan: List[Dict], max_rounds: int) -> None:
        """调整计划项的duration以确保总duration不超过max_rounds"""
        total_duration = sum(item["duration"] for item in plan)
        if total_duration > max_rounds:
            factor = max_rounds / total_duration
            for item in plan:
                item["duration"] = max(1, int(item["duration"] * factor))

            total_duration = sum(item["duration"] for item in plan)
            if total_duration < max_rounds:
                plan[-1]["duration"] += (max_rounds - total_duration)
            elif total_duration > max_rounds:
                extra = total_duration - max_rounds
                for i in reversed(range(len(plan))):
                    if plan[i]["duration"] > extra:
                        plan[i]["duration"] -= extra
                        break
                    else:
                        extra -= (plan[i]["duration"] - 1)
                        plan[i]["duration"] = 1
                        if extra == 0:
                            break

    def _generate_default_wealth(self) -> Dict[str, float]:
        """生成默认的财富数据，当LLM生成失败时使用"""
        # 基于职业和年龄设置默认金钱财富
        # 为避免固定值，添加随机变化
        base_money = 10000.0
        
        # 如果有背景信息，根据职业和年龄调整基础金钱
        if hasattr(self, 'background') and self.background:
            occupation = self.background.get("occupation", "")
            age = self.background.get("age", 25)
            
            # 根据职业设置基础金钱
            if "学生" in occupation:
                base_money = random.uniform(5000.0, 15000.0)
            elif any(job in occupation for job in ["工程师", "医生", "律师", "会计师"]):
                base_money = random.uniform(25000.0, 45000.0)
            elif any(job in occupation for job in ["教师", "公务员"]):
                base_money = random.uniform(15000.0, 30000.0)
            elif any(job in occupation for job in ["艺术家", "作家", "自由职业"]):
                base_money = random.uniform(8000.0, 25000.0)
            else:
                base_money = random.uniform(8000.0, 20000.0)
                
            # 根据年龄调整金钱（25岁以上每增加5岁增加15-25%）
            if age > 25:
                age_brackets = (age - 25) // 5
                for _ in range(age_brackets):
                    base_money *= random.uniform(1.15, 1.25)
        else:
            # 如果没有背景信息，生成随机金钱
            base_money = random.uniform(8000.0, 30000.0)
            
        # 生成其他财富值，确保有足够的随机性
        return {
            "time": round(random.uniform(-0.8, 0.8), 2),  # 更大范围的随机值
            "social": round(random.uniform(-0.8, 0.8), 2),
            "health": round(random.uniform(-0.4, 0.9), 2),
            "mental": round(random.uniform(-0.6, 0.9), 2),
            "money": round(base_money, 2)
        }

    def _set_plan_from_json(self, plan_json: str, available_locations: List[str], max_rounds: int) -> bool:
        """从JSON字符串设置智能体的计划
        
        Args:
            plan_json: 包含计划的JSON字符串
            available_locations: 可用位置列表
            max_rounds: 最大轮数
            
        Returns:
            bool: 是否成功设置计划
        """
        try:
            daily_plan = json.loads(plan_json)
            
            # 验证并清理计划
            cleaned_plan = []
            total_duration = 0
            current_location = None
            
            # 获取当前所在位置用于验证
            for loc_name, duration in zip(available_locations, [0]):
                if hasattr(self, 'id'):
                    from environment.world import World
                    world = World.get_instance()
                    if world:
                        for loc_name, loc in world.locations.items():
                            if self.id in loc.current_agents:
                                current_location = loc_name
                                break
            
            # 如果无法确定当前位置，随机选择一个
            if not current_location and available_locations:
                import random
                current_location = random.choice(available_locations)
            
            for item in daily_plan:
                # 确保必要的键存在
                if "location" not in item or "duration" not in item or "activity" not in item:
                    continue
                    
                # 确保位置是有效的
                if item["location"] not in available_locations:
                    # 替换为当前位置或随机位置
                    item["location"] = current_location if current_location else (random.choice(available_locations) if available_locations else "未知位置")
                
                # 确保duration是有效的
                try:
                    item["duration"] = int(item["duration"])
                    if item["duration"] < 1:
                        item["duration"] = 1
                except:
                    item["duration"] = 1
                
                # 如果没有状态，根据活动生成一个
                if "status" not in item or not item["status"]:
                    item["status"] = self._derive_status_from_activity(item["activity"])

                cleaned_plan.append(item)
                total_duration += item["duration"]
            
            # 确保总duration不超过max_rounds
            self._normalize_plan_durations(cleaned_plan, max_rounds)

            # 更新智能体的计划和状态
            self.daily_plan = cleaned_plan
            self.current_plan_index = 0
            if cleaned_plan:
                self.status = cleaned_plan[0]["status"]
                
            # 记录计划到短期记忆
            plan_summary = "我的今日计划:\n"
            for i, item in enumerate(cleaned_plan):
                plan_summary += f"{i+1}. 在{item['location']}停留{item['duration']}个时段，{item['activity']}。\n"
            self.add_memory(plan_summary)
            
            return True
            
        except Exception as e:
            print(f"{self.name}从JSON设置计划时出错: {e}")
            import traceback
            traceback.print_exc()
            return False 

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
- 性别: {self.gender or self.background.get('gender', '未知')}
- 年龄: {self.age or self.background.get('age', 25)}岁
- 职业: {self.background.get('occupation', '未知职业')}
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
            response = self._generate_with_llm(prompt)
            
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
        gender = self.gender or self.background.get('gender', '未知')
        if gender == "男":
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
        prompt = f"""作为{self.name}，一个{self.gender or self.background.get('gender', '未知')}性{self.age or self.background.get('age', 25)}岁{self.background.get('occupation', '未知职业')}，MBTI性格类型为{self.mbti}，我需要对今天的计划完成情况进行反思。

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
        reflection = self._generate_with_llm(prompt)
        
        # 如果生成失败，使用简化的提示重试
        if not reflection or reflection.strip() == "":
            simplified_prompt = f"作为{self.name}，MBTI类型{self.mbti}，写一段简短反思，讨论今天完成了{completion_rate}%的计划，感受如何？"
            reflection = self._generate_with_llm(simplified_prompt)
            
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
        gender = self.gender or self.background.get('gender', '未知')
        age = self.age or self.background.get('age', 25)
        prompt = f"""作为{self.name}，一个{gender}性{age}岁{self.background.get('occupation', '未知职业')}，MBTI性格类型为{self.mbti}，我需要根据我的背景和记忆制定今天的活动计划。

我的背景信息:
- 年龄: {age}岁
- 性别: {gender}
- 职业: {self.background.get('occupation', '未知职业')}
- 教育水平: {self.background.get('education', '未知')}
- 家乡: {self.background.get('hometown', '未知')}
- 外貌: {self.appearance}
- 终极目标: {self.ultimate_goal}

我当前所在位置: {current_location}

可用的位置:
{locations_text}

我的近期记忆:
{recent_short_memories_text}

我的重要长期记忆:
{key_long_memories_text}

请根据以上信息，为我制定一个符合我性格特点和背景的一天计划，包括我要去的地点、在每个地点停留的时间和我要做的事情。

计划要求:
1. 分为{max_rounds}个时间段
2. 每个时间段指定一个地点（从可用位置中选择）
3. 每个时间段1-2句话描述我计划做的事情
4. 行动计划要符合我的MBTI性格和职业背景
5. 考虑我的近期记忆中的活动和人际互动
6. 如果我最近与某人有互动，可以考虑安排与他们再次见面
7. 所有活动都应该直接或间接地服务于我的终极目标：{self.ultimate_goal}
8. 优先考虑那些能够帮助我实现终极目标的活动和社交互动

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
        plan_text = self._generate_with_llm(prompt)

        # 如果生成失败，使用默认计划
        if plan_text:
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
                        item["status"] = self._derive_status_from_activity(item["activity"])

                    cleaned_plan.append(item)
                    total_duration += item["duration"]
                
                # 确保总duration不超过max_rounds
                self._normalize_plan_durations(cleaned_plan, max_rounds)

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
                # 如果解析失败，使用默认计划（代码会在后面执行）
            
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
        
    def _init_memory_storage(self, vector_store_dir):
        """初始化记忆存储"""
        # 如果未提供vector_store_dir，使用默认值
        if not vector_store_dir:
            vector_store_dir = f"agent/history/{self.id}/vector_store"
            
        self.vector_store_dir = vector_store_dir
        os.makedirs(self.vector_store_dir, exist_ok=True)
        self.longterm_file = f"{self.vector_store_dir}/long.txt"
        self.shortterm_file = f"{self.vector_store_dir}/short.txt"
        
        # 加载记忆
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
        
    def _generate_initial_long_term_memories(self):
        """基于智能体的年龄和背景生成初始长期记忆
        
        年龄越大，生成的记忆越多，内容与智能体的背景、职业、教育和性格相关
        """
        # 如果缺少必要的属性，直接返回
        if not hasattr(self, 'age') or not self.age or not self.background or not self.name:
            print(f"无法为{self.id}生成初始记忆：缺少年龄或背景信息")
            return
            
        try:
            # 根据年龄确定生成的记忆数量
            age = int(self.age)
            # 儿童记忆较少，成年人记忆较多
            if age < 18:
                memory_count = max(3, age // 3)  # 6岁=2条，9岁=3条，15岁=5条
            elif age < 30:
                memory_count = 6 + (age - 18) // 2  # 24岁=9条，29岁=11条
            elif age < 50:
                memory_count = 12 + (age - 30) // 3  # 40岁=15条，47岁=17条
            else:
                memory_count = 18 + (age - 50) // 5  # 50岁=18条，65岁=21条
                
            # 最多生成30条记忆
            memory_count = min(memory_count, 30)
            
            # 获取智能体基本信息
            gender = self.gender or self.background.get('gender', '未知')
            occupation = self.background.get('occupation', '未知职业')
            education = self.background.get('education', '未知')
            hometown = self.background.get('hometown', '未知')
            
            # 构建提示
            prompt = f"""请为一个虚拟角色生成{memory_count}条长期记忆。

角色信息:
- 姓名: {self.name}
- 性别: {gender}
- 年龄: {age}岁
- 职业: {occupation}
- 教育程度: {education}
- 家乡: {hometown}
- MBTI性格: {self.mbti}
- 其他背景: {self.background.get('description', '')}

生成要求:
1. 生成{memory_count}条重要的长期记忆，这些记忆应该是角色人生中的关键片段
2. 记忆应按时间顺序排列，从早期记忆到近期记忆
3. 包含童年、青少年时期、成年早期、近期等不同人生阶段的记忆
4. 记忆应与角色的职业发展、教育经历、重要人际关系相关
5. 每条记忆应该是1-2句话，具体且有情感色彩
6. 使用第一人称"我"描述这些记忆
7. 符合角色的MBTI性格特点
8. 每条记忆独立成行，不要编号

记忆类型应包括:
- 重要的第一次经历
- 职业上的成就或挫折
- 重要的人际关系发展
- 人生转折点
- 具有情感意义的事件

记忆示例格式:
我5岁时第一次上台表演，紧张得几乎忘记了所有台词，但最后还是完成了演出。
大学三年级时我认识了我的挚友李明，他帮我度过了学业最困难的时期。
我28岁获得了第一次工作晋升，那天晚上我兴奋得几乎一夜未眠。

注意:
- 不要包含任何与输出格式无关的文字
- 直接输出记忆内容，每条一行
- 确保记忆符合角色的年龄、背景和性格
"""

            # 获取LLM生成的记忆
            memories = self._generate_with_llm(prompt)
            
            # 如果生成成功
            if memories and memories.strip():
                # 分割成单独的记忆条目
                memory_items = [m.strip() for m in memories.split('\n') if m.strip()]
                
                # 过滤掉可能的编号和无关信息
                filtered_memories = []
                for memory in memory_items:
                    # 移除可能的编号前缀
                    if memory[0].isdigit() and memory[1:3] in ['. ', '、', '：', ': ']:
                        memory = memory[3:].strip()
                    
                    # 如果记忆不以"我"开头，添加前缀
                    if not memory.startswith('我'):
                        memory = f"我{memory}"
                        
                    filtered_memories.append(memory)
                
                # 将记忆保存到长期记忆
                if filtered_memories:
                    with open(self.longterm_file, "w", encoding="utf-8") as f:
                        f.write('\n'.join(filtered_memories))
                    print(f"为{self.name}生成了{len(filtered_memories)}条初始长期记忆")
                    self.long_term_memory = filtered_memories
                    return
            
            # 如果生成失败，使用基础记忆
            self._generate_basic_memories()
                
        except Exception as e:
            print(f"生成初始长期记忆时出错: {e}")
            self._generate_basic_memories()
            
    def _generate_basic_memories(self):
        """生成基础的长期记忆，当LLM生成失败时使用"""
        # 基于年龄和背景生成基础记忆
        try:
            age = int(self.age)
            gender = self.gender or self.background.get('gender', '男')
            occupation = self.background.get('occupation', '职员')
            
            basic_memories = []
            
            # 童年记忆
            if age > 5:
                basic_memories.append(f"我5岁时第一次上学，感到既兴奋又紧张。")
            if age > 10:
                basic_memories.append(f"我10岁时获得了第一个学习奖项，父母非常自豪。")
                
            # 青少年记忆
            if age > 15:
                basic_memories.append(f"我初中时结交了一些好朋友，我们经常一起玩耍和学习。")
            if age > 18:
                basic_memories.append(f"我高中毕业那天，和同学们一起庆祝，充满对未来的憧憬。")
                
            # 早期成人记忆
            if age > 22:
                basic_memories.append(f"我大学期间努力学习专业知识，为未来的职业生涯打下基础。")
            if age > 25:
                basic_memories.append(f"我第一份工作是{occupation}，刚开始工作时充满热情但也面临挑战。")
                
            # 职业相关记忆
            if age > 30:
                basic_memories.append(f"我在工作中经历了第一次晋升，认识到专业能力的重要性。")
            if age > 35:
                basic_memories.append(f"我在工作中遇到了一些困难，但通过努力最终克服了。")
                
            # 中年记忆
            if age > 40:
                basic_memories.append(f"随着年龄增长，我开始重新审视生活的优先级，更注重生活质量。")
            if age > 50:
                basic_memories.append(f"步入中年后，我开始关注健康问题，调整了生活习惯。")
                
            # 近期记忆
            basic_memories.append(f"最近几年，我尝试在工作和生活中寻找平衡，学会享受当下。")
            basic_memories.append(f"我一直在思考如何能够在我的领域有所建树，留下一些成就。")
            
            # 保存基础记忆
            with open(self.longterm_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(basic_memories))
            print(f"为{self.name}生成了{len(basic_memories)}条基础长期记忆")
            self.long_term_memory = basic_memories
            
        except Exception as e:
            print(f"生成基础记忆时出错: {e}")
            # 最基本的空记忆
            self.long_term_memory = []
    
    def _get_relevant_memory(self, query):
        """获取相关的记忆"""
        if self.vector_store:
            try:
                relevant_docs = self.vector_store.similarity_search(query, k=3)
                short_term_memory = self.short_term_memory[-5:]  # 只取最近的5条短期记忆
                return relevant_docs, short_term_memory
            except Exception as e:
                print(f"查询记忆时出错: {e}")
        return [], []
    
    def _get_mbti_traits(self):
        """获取MBTI性格特点"""
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
        return mbti_descriptions.get(self.mbti, "独特的性格特点")

    def _get_llm_engine(self):
        """获取LLM引擎，如果是字符串则创建引擎对象"""
        from llm_engine.factory import LLMEngineFactory
        llm_engine = self.llm_engine
        if isinstance(llm_engine, str):
            llm_engine = LLMEngineFactory.create_engine(llm_engine)
        return llm_engine
        
    def _generate_with_llm(self, prompt):
        """使用LLM引擎生成文本"""
        llm_engine = self._get_llm_engine()
        if llm_engine is None:
            return None
        try:
            return llm_engine.generate(prompt)
        except Exception as e:
            print(f"LLM生成失败: {e}")
            return None