"""
Debate Scenario - 观点辩论场景

多人多智能体辩论场景，支持：
- 随机抽取辩题或指定辩题
- 基于MBTI性格（E/I、T/F、J/P）影响辩论风格
- 按E/I分组确保发言顺序合理
- 评估辩论表现并记录进展
"""

import random
import threading
from typing import Dict, List, Optional, Any

from simulation.scenarios.base import BaseScenario


# 预定义辩题列表
DEBATE_TOPICS = [
    {
        "id": "ai_replace_human_jobs",
        "topic": "AI是否会最终取代人类的工作？",
        "pro": "AI技术发展迅速，越来越多的工作正在被自动化取代",
        "con": "AI将创造新的就业机会，并帮助人类从事更有创造性的工作"
    },
    {
        "id": "remote_work",
        "topic": "远程办公是否应该成为未来的主流工作方式？",
        "pro": "远程办公提高效率，减少通勤时间，更好地平衡工作与生活",
        "con": "远程办公削弱团队协作，降低企业凝聚力，不利于职业发展"
    },
    {
        "id": "space_exploration",
        "topic": "人类是否应该大规模投入太空探索？",
        "pro": "太空探索推动科技发展，为人类未来生存开拓新空间",
        "con": "太空探索花费巨大，这些资源应该用于解决地球上的现实问题"
    },
    {
        "id": "social_media",
        "topic": "社交媒体对青少年成长的影响是利大于弊还是弊大于利？",
        "pro": "社交媒体帮助青少年拓展视野，获得更多信息和机会",
        "con": "社交媒体导致青少年沉迷，影响身心健康和真实社交能力"
    },
    {
        "id": "genetic_engineering",
        "topic": "基因编辑技术是否应该被允许用于人类？",
        "pro": "基因编辑可以消除遗传疾病，提升人类整体健康水平",
        "con": "基因编辑带来伦理风险，可能导致不可预测的后果"
    },
    {
        "id": "universal_basic_income",
        "topic": "全民基本收入（UBI）是否应该被实施？",
        "pro": "UBI可以消除贫困，给每个人基本的生活保障",
        "con": "UBI可能导致通货膨胀，削弱人们工作的动力"
    },
]

# 线程锁
agent_locks = {}
global_lock = threading.Lock()


class DebateScenario(BaseScenario):
    """辩论场景

    支持多人辩论，根据MBTI性格影响辩论风格。

    辩论结构：
    - 每个step一个人发言
    - 一轮 = 所有agent按speaker_order顺序发言一遍
    - total_steps = num_agents * rounds
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        self.rounds = self.config.get("rounds", 3)
        self.fast_mode = self.config.get("fast_mode", False)
        self.max_participants = self.config.get("max_participants", 8)

        self.topic = None
        self.agents_list: List[Any] = []
        self.turns_completed = 0
        self.current_round = 0
        self.speaker_order: List[str] = []

        # 辩论记录
        self.debate_record: List[Dict[str, Any]] = []

        # 快速测试模式的预设回复
        self._mock_responses = [
            "我认为这个问题需要从多个角度来看待。",
            "我不同意这个观点，让我来反驳。",
            "从逻辑上来说，这个论证存在一些问题。",
            "我有不同的看法，因为我经历过类似的情况。",
            "这个问题的答案并不是非黑即白的。",
            "让我用一个具体的例子来说明。",
            "综上所述，我认为我的立场是正确的。",
        ]

    def setup(self) -> None:
        """初始化场景"""
        self.is_initialized = True

        # 选择辩题
        topic_id = self.config.get("topic_id")
        if topic_id:
            self.topic = None
            for t in DEBATE_TOPICS:
                if t["id"] == topic_id:
                    self.topic = t
                    break
            if not self.topic:
                self.topic = random.choice(DEBATE_TOPICS)
        else:
            self.topic = random.choice(DEBATE_TOPICS)

        self.data["topic"] = self.topic
        self.data["topic_id"] = self.topic["id"]
        self.data["topic_text"] = self.topic["topic"]

    def setup_agent(self, agent) -> None:
        """设置智能体

        Args:
            agent: 智能体实例
        """
        with global_lock:
            if agent.id not in agent_locks:
                agent_locks[agent.id] = threading.Lock()

        # 确定辩论立场（根据config或随机分配）
        stance = self.config.get(f"stance_{agent.id}")
        if not stance:
            stance = "pro" if random.random() < 0.5 else "con"

        agent.debate_stance = stance
        agent.debate_score = 0.0

        if agent not in self.agents_list:
            self.agents_list.append(agent)

    def get_prompt_for_agent(self, agent, context: Dict[str, Any]) -> str:
        """获取智能体的提示词

        Args:
            agent: 智能体实例
            context: 上下文信息

        Returns:
            str: 提示词
        """
        topic = self.topic
        stance = getattr(agent, "debate_stance", "pro")
        stance_text = "正方" if stance == "pro" else "反方"
        mbti = getattr(agent, "mbti", "INTJ")

        # 提取MBTI维度
        e_or_i = mbti[0] if len(mbti) >= 1 else "I"
        s_or_n = mbti[1] if len(mbti) >= 2 else "N"
        t_or_f = mbti[2] if len(mbti) >= 3 else "T"
        j_or_p = mbti[3] if len(mbti) >= 4 else "J"

        # 根据性格构建提示词
        prompt_parts = [
            f"【辩论场景】辩题：{topic['topic']}",
            f"你的角色：{agent.name}",
            f"你的立场：{stance_text}（{'支持' if stance == 'pro' else '反对'}）",
        ]

        if stance == "pro":
            prompt_parts.append(f"正方核心论点：{topic['pro']}")
        else:
            prompt_parts.append(f"反方核心论点：{topic['con']}")

        # MBTI性格影响辩论风格
        style_notes = []

        if e_or_i == "E":
            style_notes.append("你是一个外向的人，喜欢与他人交流和互动。你倾向于积极发言，主动表达观点。")
        else:
            style_notes.append("你是一个内向的人，更喜欢深思熟虑后发言。你的观点往往更有深度。")

        if t_or_f == "T":
            style_notes.append("你倾向于理性思考，注重逻辑和证据。你的辩论风格偏向逻辑分析。")
        else:
            style_notes.append("你倾向于情感共鸣，注重价值观和人的感受。你的辩论风格偏向情感诉求。")

        if j_or_p == "J":
            style_notes.append("你喜欢有结构和有组织的表达方式，论点清晰有序。")
        else:
            style_notes.append("你更喜欢灵活和开放的表达方式，善于即兴发挥。")

        prompt_parts.append(" ".join(style_notes))

        # 添加辩论历史
        if self.debate_record:
            prompt_parts.append("\n【辩论历史】")
            for record in self.debate_record[-3:]:
                prompt_parts.append(f"- {record['speaker']}：{record['content'][:100]}...")

        prompt_parts.append(f"\n请以{agent.name}的身份发表你的辩论发言。")

        return "\n".join(prompt_parts)

    def evaluate_action(self, agent, action: Dict[str, Any]) -> Dict[str, Any]:
        """评估智能体的辩论表现

        Args:
            agent: 智能体实例
            action: 行动字典

        Returns:
            Dict[str, Any]: 评估结果，包含score和reason
        """
        action_type = action.get("type", "unknown")
        content = action.get("content", "")

        score = 0.0
        reason = ""

        if action_type == "debate_speak":
            content_length = len(content)

            # 基础分：内容长度适当
            if 20 <= content_length <= 300:
                score += 0.3
                reason += "内容长度适中。"
            elif content_length < 20:
                score -= 0.2
                reason += "内容过短。"
            elif content_length > 300:
                score -= 0.1
                reason += "内容过长。"

            # MBTI影响评分
            mbti = getattr(agent, "mbti", "INTJ")
            t_or_f = mbti[2] if len(mbti) >= 3 else "T"

            # 检查是否有逻辑关键词（T型）或情感关键词（F型）
            if t_or_f == "T":
                logical_words = ["因为", "所以", "逻辑", "证明", "分析", "因此", "推理", "证据"]
                if any(word in content for word in logical_words):
                    score += 0.3
                    reason += "展示了逻辑思维。"
            else:
                emotional_words = ["感受", "觉得", "相信", "关心", "在乎", "价值", "意义"]
                if any(word in content for word in emotional_words):
                    score += 0.3
                    reason += "展现了情感共鸣。"

            # 检查是否有反驳
            rebuttal_words = ["反对", "不同意", "不对", "但是", "然而", "反驳"]
            if any(word in content for word in rebuttal_words):
                score += 0.2
                reason += "有反驳意识。"

            # 检查是否有例子
            example_words = ["比如", "例如", "比如说", "就像"]
            if any(word in content for word in example_words):
                score += 0.2
                reason += "善用举例。"

        elif action_type == "debate_support":
            # 支持他人观点
            score = 0.15
            reason = "支持了其他辩手的观点。"

        elif action_type == "debate_attack":
            # 攻击他人观点
            score = -0.1
            reason = "攻击性过强，可能影响辩论氛围。"

        # 更新智能体的辩论分数
        current_score = getattr(agent, "debate_score", 0.0)
        agent.debate_score = current_score + score

        return {
            "score": score,
            "reason": reason if reason else "无特殊评价。"
        }

    def step(
        self,
        agents: Dict[str, Any],
        environment: Any,
        step: int
    ) -> Dict[str, Any]:
        """执行一步模拟

        每个step一个人发言。
        一轮 = 所有agent按顺序发言一遍。

        Args:
            agents: 智能体字典
            environment: 环境实例
            step: 当前步数（从1开始）

        Returns:
            Dict[str, Any]: 步进结果
        """
        self.result["steps"] = step

        # 如果还没有speaker_order，先计算
        if not self.speaker_order and self.agents_list:
            self._compute_speaker_order()

        num_agents = len(self.agents_list)
        if num_agents == 0:
            return {
                "turns_completed": 0,
                "debate_progress": "等待参与者",
                "topic": self.topic["topic"] if self.topic else "",
                "rounds": self.rounds,
                "speakers": []
            }

        # 计算当前是第几轮和第几轮中的第几个
        # step 1-6 = round 1, step 7-12 = round 2, etc. (for 6 agents)
        self.current_round = (step - 1) // num_agents + 1

        # 确定当前step应该发言的agent
        speaker_idx_in_order = (step - 1) % num_agents
        current_speaker_id = self.speaker_order[speaker_idx_in_order] if speaker_idx_in_order < len(self.speaker_order) else None

        step_result = {
            "turns_completed": self.turns_completed,
            "debate_progress": f"第{self.current_round}/{self.rounds}轮辩论",
            "topic": self.topic["topic"] if self.topic else "",
            "rounds": self.rounds,
            "speakers": []
        }

        if current_speaker_id is None or current_speaker_id not in agents:
            return step_result

        current_agent = agents[current_speaker_id]

        # 获取回复
        response = ""
        try:
            response = self._get_debate_response(current_agent)
        except Exception:
            response = random.choice(self._mock_responses)

        # 只有非空回复才记录
        if response and response.strip():
            # 评估
            evaluation = self.evaluate_action(current_agent, {
                "type": "debate_speak",
                "content": response
            })

            record = {
                "speaker": current_agent.name,
                "agent_id": current_agent.id,
                "content": response,
                "score": evaluation["score"],
                "reason": evaluation["reason"],
                "round": self.current_round,
                "step": step
            }
            self.debate_record.append(record)

            step_result["speakers"].append({
                "name": current_agent.name,
                "stance": getattr(current_agent, "debate_stance", "unknown"),
                "score": evaluation["score"],
                "content": response[:50] + "..." if len(response) > 50 else response
            })

            self.turns_completed += 1
            step_result["turns_completed"] = self.turns_completed

        # 检查是否完成：一轮 = num_agents个step
        total_steps_needed = num_agents * self.rounds
        if step >= total_steps_needed:
            self._compute_final_results()
            self.set_completed(f"完成{self.rounds}轮辩论，共{self.turns_completed}次有效发言")

        return step_result

    def _compute_speaker_order(self) -> None:
        """计算发言顺序，按E/I分组"""
        e_agents = []
        i_agents = []

        for agent in self.agents_list:
            mbti = getattr(agent, "mbti", "I")
            if mbti.startswith("E"):
                e_agents.append(agent.id)
            else:
                i_agents.append(agent.id)

        # 交替排列：E-I-E-I-...确保每个人都有发言机会
        self.speaker_order = []
        max_len = max(len(e_agents), len(i_agents))

        for i in range(max_len):
            if i < len(e_agents):
                self.speaker_order.append(e_agents[i])
            if i < len(i_agents):
                self.speaker_order.append(i_agents[i])

        # 如果一方人少，另一方补充
        for agent in self.agents_list:
            if agent.id not in self.speaker_order:
                self.speaker_order.append(agent.id)

    def _get_debate_response(self, agent) -> str:
        """获取辩论回复

        Args:
            agent: 智能体

        Returns:
            str: 回复内容
        """
        context = {}
        prompt = self.get_prompt_for_agent(agent, context)

        if self.fast_mode:
            return random.choice(self._mock_responses)

        with agent_locks.get(agent.id, global_lock):
            if hasattr(agent, "think"):
                return agent.think(prompt)
            return random.choice(self._mock_responses)

    def _compute_final_results(self) -> None:
        """计算最终辩论结果"""
        pro_score = 0.0
        con_score = 0.0
        pro_count = 0
        con_count = 0

        for record in self.debate_record:
            agent_id = record["agent_id"]
            agent = None
            for a in self.agents_list:
                if a.id == agent_id:
                    agent = a
                    break
            if not agent:
                continue

            stance = getattr(agent, "debate_stance", "pro")
            score = record["score"]

            if stance == "pro":
                pro_score += score
                pro_count += 1
            else:
                con_score += score
                con_count += 1

        winner = "pro" if pro_score > con_score else "con" if con_score > pro_score else "tie"

        self.data["results"] = {
            "pro_score": pro_score,
            "con_score": con_score,
            "pro_count": pro_count,
            "con_count": con_count,
            "winner": winner,
            "total_turns": self.turns_completed,
            "records": self.debate_record
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取场景总结

        Returns:
            Dict[str, Any]: 场景总结
        """
        summary = super().get_summary()
        summary["data"]["topic"] = self.topic
        summary["data"]["turns_completed"] = self.turns_completed
        summary["data"]["speaker_order"] = self.speaker_order

        if "results" in self.data:
            summary["data"]["results"] = self.data["results"]

        return summary
