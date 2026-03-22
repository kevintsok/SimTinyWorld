"""
Daily Life Scenario - 日常生活场景

模拟智能体的日常生活对话场景，包括：
- 智能体制定日常计划
- 位置移动和对话交互
- 心情和财富状态更新
"""

import random
import threading
import time
from typing import Dict, List, Optional, Any

from simulation.scenarios.base import BaseScenario


class DailyLifeScenario(BaseScenario):
    """日常生活场景

    模拟智能体的日常生活，包括制定计划、移动、对话等活动。
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        # 配置参数
        self.days = self.config.get("days", 3)
        self.rounds_per_day = self.config.get("rounds_per_day", 5)
        self.max_participants = self.config.get("max_participants", 4)
        self.fast_mode = self.config.get("fast_mode", False)

        # 环境引用
        self.world = None

        # 位置信息
        self.available_locations = []
        self.location_descriptions = {}

        # 初始化锁字典（改为实例变量，避免多实例共享）
        self.agent_locks = {}
        self.global_lock = threading.Lock()

    def setup(self) -> None:
        """初始化场景"""
        self.is_initialized = True

        # 设置位置信息（DailyLifeScenario使用self.world）
        env = getattr(self, 'world', None) or self.environment
        if env and hasattr(env, "locations"):
            self.available_locations = list(env.locations.keys())
            self.location_descriptions = {
                loc: getattr(env.locations[loc], "description", "")
                for loc in self.available_locations
            }

    def setup_agent(self, agent) -> None:
        """设置智能体

        Args:
            agent: 智能体实例
        """
        # 确保智能体有锁
        with self.global_lock:
            if agent.id not in self.agent_locks:
                self.agent_locks[agent.id] = threading.Lock()

    def _get_agent_location(self, agent_id: str, environment: Any) -> Optional[str]:
        """获取智能体当前位置的辅助方法"""
        if hasattr(environment, "get_agent_location"):
            return environment.get_agent_location(agent_id)
        if hasattr(environment, "locations"):
            for loc_name, loc in environment.locations.items():
                if agent_id in getattr(loc, "current_agents", set()):
                    return loc_name
        return None

    def get_prompt_for_agent(self, agent, context: Dict[str, Any]) -> str:
        """获取智能体的提示词

        Args:
            agent: 智能体实例
            context: 上下文信息

        Returns:
            str: 提示词
        """
        location = context.get("location", "未知地点")
        others = context.get("other_agents", [])

        prompt = f"我们现在在{location}。"
        if others:
            others_str = "、".join([a.name for a in others])
            prompt += f" 还有{others_str}也在场。"

        return prompt

    def evaluate_action(self, agent, action: Dict[str, Any]) -> Dict[str, Any]:
        """评估智能体的行动

        Args:
            agent: 智能体实例
            action: 行动字典

        Returns:
            Dict[str, Any]: 评估结果
        """
        action_type = action.get("type", "unknown")
        result = {"accepted": True, "feedback": ""}

        # 根据行动类型进行评估
        if action_type == "move":
            # 移动行动
            target = action.get("target", "")
            if target in self.available_locations:
                result["accepted"] = True
            else:
                result["accepted"] = False
                result["feedback"] = f"位置 '{target}' 不存在"

        elif action_type == "speak":
            # 对话行动
            content = action.get("content", "")
            if len(content) > 500:
                result["accepted"] = False
                result["feedback"] = "对话内容过长"

        return result

    def step(
        self,
        agents: Dict[str, Any],
        environment: Any,
        step: int
    ) -> Dict[str, Any]:
        """执行一步模拟

        Args:
            agents: 智能体字典
            environment: 环境实例
            step: 当前步数

        Returns:
            Dict[str, Any]: 步进结果
        """
        self.result["steps"] = step
        self.world = environment

        # 计算当前是第几天
        day = (step - 1) // self.rounds_per_day + 1
        round_in_day = (step - 1) % self.rounds_per_day + 1

        step_result = {
            "day": day,
            "round": round_in_day,
            "dialogues": [],
            "movements": []
        }

        # 第一轮：制定计划
        if round_in_day == 1:
            self._plan_day(agents)

        # 移动阶段
        self._move_agents(agents, environment, step_result)

        # 对话阶段
        self._run_dialogues(agents, environment, step_result)

        # 最后一天最后一轮：更新财富和休息
        if round_in_day == self.rounds_per_day:
            if day == self.days:
                self._update_wealth(agents, environment)
                self._rest_agents(agents)

                # 场景完成
                self.set_completed(f"完成了 {self.days} 天的模拟")

        return step_result

    def _plan_day(self, agents: Dict[str, Any]) -> None:
        """让智能体制定当天计划

        Args:
            agents: 智能体字典
        """
        if self.fast_mode:
            # 快速模式：跳过计划，直接为每个智能体随机分配位置
            for agent in agents.values():
                if hasattr(agent, 'daily_plan'):
                    agent.daily_plan = [
                        {
                            "location": random.choice(self.available_locations),
                            "duration": 1,
                            "activity": "随机活动",
                            "status": "活动中"
                        }
                        for _ in range(self.rounds_per_day)
                    ]
            return

        agent_list = list(agents.values())

        for agent in agent_list:
            try:
                if hasattr(agent, "plan"):
                    agent.plan(
                        self.available_locations,
                        self.location_descriptions,
                        self.rounds_per_day
                    )
            except Exception as e:
                print(f"{agent.name} 制定计划时出错: {e}")

    def _move_agents(
        self,
        agents: Dict[str, Any],
        environment: Any,
        step_result: Dict[str, Any]
    ) -> None:
        """移动智能体

        Args:
            agents: 智能体字典
            environment: 环境实例
            step_result: 步进结果
        """
        if not environment:
            return

        agent_list = list(agents.values())

        for agent in agent_list:
            try:
                # 获取计划的下一个位置
                if hasattr(agent, "get_next_planned_location"):
                    next_location = agent.get_next_planned_location()
                else:
                    next_location = None

                if next_location:
                    # 获取当前位置
                    current_location = self._get_agent_location(agent.id, environment)

                    # 如果位置不同，移动智能体
                    if current_location and next_location != current_location:
                        if hasattr(environment, "move_agent"):
                            environment.move_agent(agent, current_location, next_location)

                        memory = f"我从{current_location}移动到了{next_location}。"
                        agent.add_memory(memory)

                        step_result["movements"].append({
                            "agent": agent.name,
                            "from": current_location,
                            "to": next_location
                        })
            except Exception as e:
                print(f"{agent.name} 移动时出错: {e}")

    def _run_dialogues(
        self,
        agents: Dict[str, Any],
        environment: Any,
        step_result: Dict[str, Any]
    ) -> None:
        """运行对话

        Args:
            agents: 智能体字典
            environment: 环境实例
            step_result: 步进结果
        """
        if not environment:
            return

        # 按位置分组智能体
        location_agents = {}

        if hasattr(environment, "locations"):
            for loc_name, loc in environment.locations.items():
                location_agents[loc_name] = []
                agent_ids = getattr(loc, "current_agents", set())
                for agent_id in agent_ids:
                    if agent_id in agents:
                        location_agents[loc_name].append(agents[agent_id])
        else:
            # 如果环境没有locations，直接使用所有智能体
            location_agents["default"] = list(agents.values())

        # 在每个位置运行对话
        dialogue_threads = []
        for loc_name, loc_agents in location_agents.items():
            if loc_agents:
                thread = threading.Thread(
                    target=self._run_dialogue_thread,
                    args=(loc_agents, loc_name, step_result)
                )
                dialogue_threads.append(thread)
                thread.start()

        # 等待所有对话完成
        for thread in dialogue_threads:
            thread.join()

    def _run_dialogue_thread(
        self,
        agents: List[Any],
        location: str,
        step_result: Dict[str, Any]
    ) -> None:
        """在单独线程中运行对话

        Args:
            agents: 智能体列表
            location: 位置
            step_result: 步进结果
        """
        # 复制列表避免多线程冲突
        participating_agents = agents.copy()

        # 限制参与者数量
        if len(participating_agents) > self.max_participants:
            participating_agents = random.sample(participating_agents, self.max_participants)

        # 确保有锁
        for agent in participating_agents:
            with self.global_lock:
                if agent.id not in self.agent_locks:
                    self.agent_locks[agent.id] = threading.Lock()

        # 只有一个智能体，记录独处
        if len(participating_agents) < 2:
            if participating_agents:
                solo_agent = participating_agents[0]
                thought = f"我在{location}，周围没有其他人，感到{solo_agent.mood.get('description', '平静')}。"

                with self.agent_locks.get(solo_agent.id, self.global_lock):
                    solo_agent.add_memory(thought)

                return

        # 开始对话
        self._run_dialogue(participating_agents, location, step_result)

    def _run_dialogue(
        self,
        agents: List[Any],
        location: str,
        step_result: Dict[str, Any]
    ) -> None:
        """运行一轮对话 - 持续进行直到自然结束

        Args:
            agents: 智能体列表
            location: 位置
            step_result: 步进结果
        """
        # 获取地点描述（DailyLifeScenario使用self.world）
        loc_desc = ""
        if hasattr(self, 'world') and self.world and hasattr(self.world, 'locations'):
            loc = self.world.locations.get(location)
            if loc and hasattr(loc, 'description'):
                loc_desc = loc.description

        # 记录说过再见的智能体
        said_goodbye = set()

        # 完整对话记录
        full_dialogue = []

        # 对话历史（用于传递上下文）
        conversation_history = []

        # 选择起始发言者
        last_speaker = None

        # 对话轮次计数
        round_count = 0

        while True:
            round_count += 1

            # 选择下一个发言者（允许重复选择，让对话流动）
            next_speaker = self._select_next_speaker(
                agents, last_speaker, said_goodbye, conversation_history
            )

            if next_speaker is None:
                break

            # 构建提示
            query = self._build_dialogue_query(
                next_speaker, agents, location, loc_desc, conversation_history, last_speaker
            )

            # 获取回复
            response = self._get_dialogue_response(next_speaker, query, conversation_history)

            # 打印和记录
            print(f"{next_speaker.name}: {response}")
            full_dialogue.append({"speaker": next_speaker.name, "content": response})

            # 记录到对话历史
            conversation_history.append({"speaker": next_speaker.name, "content": response})

            # 记忆
            memory_text = f"在{location}，我对大家说：'{response}'"
            with self.agent_locks.get(next_speaker.id, self.global_lock):
                next_speaker.add_memory(memory_text)

            # 其他人听到对话
            for agent in agents:
                if agent.id != next_speaker.id:
                    hearing_memory = f'在{location}，{next_speaker.name}说："{response}"'
                    with self.agent_locks.get(agent.id, self.global_lock):
                        agent.add_memory(hearing_memory)

            # 更新心情
            self._update_mood_from_response(next_speaker, response, location)

            # 检查是否说再见
            if "再见" in response or "拜拜" in response:
                said_goodbye.add(next_speaker.id)

            # 改进的结束检测
            should_end = False

            # 条件1：超过80%说再见
            if len(said_goodbye) >= len(agents) * 0.8:
                should_end = True
            # 条件2：对话轮次过多（最多12轮）
            elif len(conversation_history) > 12:
                should_end = True
            # 条件3：连续3轮都是短回复（客套话）
            elif len(conversation_history) >= 3:
                recent = conversation_history[-3:]
                if all(len(h['content']) < 10 for h in recent):
                    should_end = True
            # 条件4：LLM判断对话是否结束（只有对话超过4轮才判断）
            elif len(conversation_history) >= 4 and not self.fast_mode:
                try:
                    if next_speaker.should_conversation_end(conversation_history[-3:]):
                        should_end = True
                except Exception as e:
                    pass  # 如果判断失败，继续对话

            if should_end:
                break

            last_speaker = next_speaker
            self._last_response = response

        step_result["dialogues"].append({
            "location": location,
            "participants": [a.name for a in agents],
            "lines": full_dialogue
        })

    def _select_next_speaker(
        self,
        agents: List[Any],
        last_speaker: Any,
        said_goodbye: set,
        conversation_history: List[Dict]
    ) -> Any:
        """选择下一个发言者

        Args:
            agents: 智能体列表
            last_speaker: 上一个发言者
            said_goodbye: 已说再见的智能体ID集合
            conversation_history: 对话历史

        Returns:
            下一个发言的智能体，如果没有可用智能体则返回None
        """
        available = [a for a in agents if a.id not in said_goodbye]
        if not available:
            return None

        # 第一个发言者
        if last_speaker is None:
            return random.choice(agents)

        # 尝试选择被提到的智能体
        mentioned = []
        last_response = getattr(self, '_last_response', '')
        for a in available:
            if a.id != last_speaker.id and last_response:
                if a.name in last_response:
                    mentioned.append(a)

        if mentioned and random.random() < 0.8:
            # E型优先接话
            e_mentioned = [a for a in mentioned if a.mbti and a.mbti.startswith('E')]
            if e_mentioned and random.random() < 0.6:
                return random.choice(e_mentioned)
            else:
                return random.choice(mentioned)
        else:
            candidates = [a for a in available if a.id != last_speaker.id]
            if not candidates:
                return None

            # 加权选择：E型略高概率
            weights = []
            for a in candidates:
                weight = 1.0 if not (a.mbti and a.mbti.startswith('I')) else 0.6
                weights.append(weight)
            total = sum(weights)
            r = random.random() * total
            cumsum = 0
            for idx, a in enumerate(candidates):
                cumsum += weights[idx]
                if r <= cumsum:
                    return a
            return candidates[0]

    def _build_dialogue_query(
        self,
        speaker: Any,
        agents: List[Any],
        location: str,
        loc_desc: str,
        conversation_history: List[Dict],
        last_speaker: Any
    ) -> str:
        """构建对话提示

        Args:
            speaker: 当前发言者
            agents: 所有智能体列表
            location: 位置名称
            loc_desc: 位置描述
            conversation_history: 对话历史
            last_speaker: 上一个发言者

        Returns:
            str: 提示文本
        """
        # 第一个发言者 - 场景感知的开场
        if not conversation_history:
            others = [a for a in agents if a.id != speaker.id]
            others_info = "、".join([f"{a.name}({a.mbti})" for a in others])

            return f"""你是{speaker.name}，性格是{speaker.mbti}。

你现在在{location}，这里是{loc_desc or '一个普通的室内空间'}。
你身边有：{others_info}。

请根据你的性格和当前场景，自然地发起一段对话。
开场白应该：
1. 与当前场景和地点相关
2. 符合你的MBTI性格
3. 自然、不生硬，像真实的人际交流

只需要生成一句开场白，不要说"作为XX"这样的话。"""

        # 继续对话 - 包含历史
        recent_history = conversation_history[-4:]
        history_str = "\n".join([f"{h['speaker']}说：'{h['content']}'" for h in recent_history])

        others = [a for a in agents if a.id != speaker.id]
        others_str = "、".join([a.name for a in others])

        return f"""最近的对话：
{history_str}

现在{last_speaker.name}说了：'{self._last_response}'
我们在{location}，还有{others_str}也在场。
请自然地接话，保持话题连贯性。"""

    def _get_dialogue_response(
        self,
        speaker: Any,
        query: str,
        conversation_history: List[Dict]
    ) -> str:
        """获取智能体回复

        Args:
            speaker: 发言者
            query: 提示文本
            conversation_history: 对话历史

        Returns:
            str: 回复内容
        """
        try:
            if self.fast_mode:
                # 快速测试模式：根据对话阶段选择回复类型
                return self._get_mock_response(conversation_history)
            else:
                with self.agent_locks.get(speaker.id, self.global_lock):
                    history = conversation_history[-4:] if conversation_history else []
                    if hasattr(speaker, 'think'):
                        return speaker.think(query, history=history)
                    return ""
        except Exception as e:
            print(f"对话响应出错: {e}")
            return "（看起来有些犹豫，没有说话）"

    def _get_mock_response(self, conversation_history: List[Dict]) -> str:
        """快速测试模式下的mock回复

        Args:
            conversation_history: 对话历史

        Returns:
            str: 模拟回复
        """
        # 防御性检查：确保conversation_history是有效列表
        if conversation_history is None:
            conversation_history = []

        # 根据对话深度选择回复类型
        if not conversation_history:
            # 开场白
            responses = [
                "你好，很高兴见到大家！",
                "今天天气真不错啊。",
                "大家都在这儿呢，有什么新鲜事吗？",
            ]
        elif len(conversation_history) >= 3 and len(conversation_history) % 3 == 0:
            # 每3轮考虑说再见
            if random.random() < 0.3:
                return "好了，我先走了，大家回见！"
            responses = [
                "嗯，我同意你的看法。",
                "是吗？那确实是这样。",
                "有道理，让我想想...",
            ]
        else:
            responses = [
                "嗯，这个话题挺有意思的。",
                "我倒是没想过这个问题。",
                "你说得对，我也这么觉得。",
                "那后来怎么样了呢？",
            ]

        # 再次防御性检查
        if not responses:
            return "嗯..."
        return random.choice(responses)

    def _update_mood_from_response(
        self,
        agent: Any,
        response: str,
        location: str
    ) -> None:
        """根据回复更新心情

        Args:
            agent: 智能体
            response: 回复内容
            location: 位置
        """
        response_lower = response.lower()

        with self.agent_locks.get(agent.id, self.global_lock):
            if any(word in response_lower for word in ["高兴", "开心", "愉快", "喜欢"]):
                agent.update_mood('positive', 0.15, f"在{location}进行愉快的对话")
            elif any(word in response_lower for word in ["烦", "讨厌", "生气", "不满"]):
                agent.update_mood('negative', -0.15, f"在{location}进行不愉快的对话")
            else:
                # 根据MBTI更新
                mbti = getattr(agent, "mbti", "I")
                if mbti.startswith('E'):
                    agent.update_mood('social', 0.05, f"在{location}参与对话")
                else:
                    agent.update_mood('social', -0.02, f"在{location}不得不社交")

    def _update_wealth(self, agents: Dict[str, Any], environment: Any) -> None:
        """更新智能体财富

        Args:
            agents: 智能体字典
            environment: 环境实例
        """
        if self.fast_mode:
            return  # 快速模式跳过财富更新

        agent_list = list(agents.values())

        for agent in agent_list:
            if not hasattr(agent, "wealth") or not hasattr(agent, "short_term_memory"):
                continue

            # 获取最近记忆
            recent = agent.short_term_memory[-3:] if agent.short_term_memory else []
            # short_term_memory是字符串列表
            activities = "\n".join([m if isinstance(m, str) else getattr(m, 'content', str(m)) for m in recent])

            if not activities:
                continue

            # 构建评估提示
            current_location = self._get_agent_location(agent.id, environment) or ""

            prompt = f"""评估智能体 {agent.name} 的财富变化。

当前财富状态:
- 时间财富: {agent.wealth.get("time", 0):.2f}
- 社交财富: {agent.wealth.get("social", 0):.2f}
- 健康财富: {agent.wealth.get("health", 0):.2f}
- 精神财富: {agent.wealth.get("mental", 0):.2f}
- 金钱财富: {agent.wealth.get("money", 0):.2f}元

最近活动:
{activities}

返回JSON格式的财富变化:
{{
  "time_change": -0.1到0.1,
  "social_change": -0.1到0.1,
  "health_change": -0.1到0.1,
  "mental_change": -0.1到0.1,
  "money_change": -500到500,
  "reason": "变化原因"
}}
"""

            try:
                # 调用LLM评估（如果智能体有这个方法）
                if hasattr(agent, "_generate_with_llm"):
                    result = agent._generate_with_llm(prompt)
                    # 解析JSON并更新（简化处理）
                    # 实际实现需要完整的JSON解析
                    pass
            except Exception as e:
                print(f"评估{agent.name}财富时出错: {e}")

    def _rest_agents(self, agents: Dict[str, Any]) -> None:
        """让智能体休息

        Args:
            agents: 智能体字典
        """
        if self.fast_mode:
            return  # 快速模式跳过休息

        agent_list = list(agents.values())

        for agent in agent_list:
            try:
                if hasattr(agent, "sleep"):
                    agent.sleep()
            except Exception as e:
                print(f"{agent.name} 休息时出错: {e}")

    # ===== 序列化支持 =====

    def to_dict(self) -> Dict[str, Any]:
        """将场景转换为字典表示

        Returns:
            Dict[str, Any]: 场景状态字典
        """
        return {
            "days": self.days,
            "rounds_per_day": self.rounds_per_day,
            "max_participants": self.max_participants,
            "fast_mode": self.fast_mode,
            "is_initialized": self.is_initialized,
            "is_completed": self.is_completed,
            "available_locations": self.available_locations,
            "location_descriptions": self.location_descriptions,
            "result": self.result,
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], config: Dict[str, Any] = None) -> "DailyLifeScenario":
        """从字典创建场景实例

        Args:
            data: 场景状态字典
            config: 配置字典（可选）

        Returns:
            DailyLifeScenario: 恢复的场景实例
        """
        # 使用配置创建新实例
        scenario = cls(config or {})

        # 恢复配置参数
        scenario.days = data.get("days", 3)
        scenario.rounds_per_day = data.get("rounds_per_day", 5)
        scenario.max_participants = data.get("max_participants", 4)
        scenario.fast_mode = data.get("fast_mode", False)

        # 恢复状态
        scenario.is_initialized = data.get("is_initialized", False)
        scenario.is_completed = data.get("is_completed", False)
        scenario.available_locations = data.get("available_locations", [])
        scenario.location_descriptions = data.get("location_descriptions", {})
        scenario.result = data.get("result", {"steps": 0, "events": [], "summary": ""})
        scenario.data = data.get("data", {})

        # 不序列化锁，恢复时重建
        scenario.agent_locks = {}
        scenario.global_lock = threading.Lock()

        return scenario
