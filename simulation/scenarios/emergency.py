"""
Emergency Scenario - 突发事件场景

模拟社会突发事件的应对场景，包括：
- 地震、经济危机、疫情、洪水等事件
- Agent协作应对减少负面影响
- 自私行为加剧负面影响
"""

import random
from typing import Dict, List, Optional, Any

from simulation.scenarios.base import BaseScenario


EMERGENCY_TYPES = ["earthquake", "economic_crisis", "pandemic", "flood"]

COOPERATIVE_KEYWORDS = [
    "帮助", "救援", "捐", "支援", "合作", "分享", "团结", "互助",
    "救治", "疏散", "安置", "捐赠", "志愿者", "奉献", "牺牲", "协助"
]
SELFISH_KEYWORDS = [
    "逃跑", "囤积", "抢购", "独自", "自私", "不管", "不救", "离开",
    "抛弃", "只顾", "占有", "藏起来", "躲避", "趁火打劫"
]


class EmergencyScenario(BaseScenario):
    """突发事件场景

    模拟Agent应对社会突发事件的场景。
    事件类型包括地震、经济危机、疫情、洪水等。
    Agent的协作行为可以降低事件负面影响，自私行为会加剧损失。
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        self.max_rounds = self.config.get("rounds", 10)
        self.fast_mode = self.config.get("fast_mode", False)
        self.initial_population = self.config.get("agents", 10)

        self.emergency_type = None
        self.severity = 0.0
        self.duration = 0
        self.remaining_duration = 0
        self.impact_range = 1.0

        self.initial_health = 1.0
        self.initial_wealth = 1.0
        self.current_health = 1.0
        self.current_wealth = 1.0

        self.total_deaths = 0
        self.economic_losses = 0.0
        self.deaths_prevented = 0
        self.economic_loss_reduced = 0.0

        self.agent_actions: Dict[str, List[Dict]] = {}
        self.cooperation_score = 0.0
        self.selfish_score = 0.0

        # 快速测试模式的预设回复
        self._mock_responses = [
            "我愿意帮助受灾的人们，大家都需要团结一心。",
            "我们应该组织救援队伍，分配物资给最需要的人。",
            "作为社区的一员，我必须为大家的安全贡献力量。",
            "我选择参与志愿服务，帮助维持秩序和分发物资。",
            "这种时候更要相互扶持，共渡难关。",
            "我决定捐出部分物资给灾民。",
            "自私的行为只会让情况更糟，我们应该合作。"
        ]

    def setup(self) -> None:
        """初始化场景"""
        self.is_initialized = True

        # 随机选择事件类型
        self.emergency_type = random.choice(EMERGENCY_TYPES)

        # 根据事件类型设置初始严重程度和持续时间
        if self.emergency_type == "earthquake":
            self.severity = random.uniform(0.5, 0.9)
            self.duration = random.randint(3, 5)
            self.impact_range = random.uniform(0.6, 0.9)
        elif self.emergency_type == "economic_crisis":
            self.severity = random.uniform(0.4, 0.7)
            self.duration = random.randint(5, 8)
            self.impact_range = random.uniform(0.7, 1.0)
        elif self.emergency_type == "pandemic":
            self.severity = random.uniform(0.5, 0.8)
            self.duration = random.randint(4, 7)
            self.impact_range = random.uniform(0.8, 1.0)
        elif self.emergency_type == "flood":
            self.severity = random.uniform(0.4, 0.8)
            self.duration = random.randint(3, 6)
            self.impact_range = random.uniform(0.5, 0.8)

        self.remaining_duration = self.duration

        # 初始化数据
        self.data = {
            "emergency_type": self.emergency_type,
            "severity": self.severity,
            "duration": self.duration,
            "impact_range": self.impact_range,
            "initial_agents": self.initial_population,
        }

        # 记录事件
        self.add_event({
            "type": "emergency_start",
            "emergency": self.emergency_type,
            "severity": self.severity,
            "round": 0
        })

    def get_prompt_for_agent(self, agent, context: Dict[str, Any]) -> str:
        """获取智能体的提示词

        Args:
            agent: 智能体实例
            context: 上下文信息

        Returns:
            str: 提示词
        """
        emergency_names = {
            "earthquake": "强烈地震",
            "economic_crisis": "经济危机",
            "pandemic": "疫情爆发",
            "flood": "洪涝灾害"
        }
        emergency_name = emergency_names.get(self.emergency_type, self.emergency_type)

        # 获取agent当前的健康和财富状态
        health = getattr(agent, "wealth", {}).get("health", 0.5)
        money = getattr(agent, "wealth", {}).get("money", 10000)

        prompt = f"""【突发事件应急响应】

当前发生{emergency_name}，这是一起严重的{self.emergency_type}突发事件！
- 事件严重程度: {self.severity:.0%}
- 影响范围: {self.impact_range:.0%}
- 剩余持续时间: {self.remaining_duration}轮

你的当前状态:
- 健康状态: {health:.0%}
- 经济状况: {money:.0f}元

请决定你在这个紧急情况下的行为。你的行为将被评估为：
1. 协作行为（帮助他人、分享资源、参与救援等）= 减少事件负面影响
2. 自私行为（囤积物资、独自逃生、趁火打劫等）= 加剧事件负面影响

请描述你的行动。回复格式：
"我决定[具体行为]，因为[原因]。"
"""
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
        content = action.get("content", "")
        result = {"accepted": True, "feedback": "", "impact": 0.0}

        # 初始化agent的action追踪
        if agent.id not in self.agent_actions:
            self.agent_actions[agent.id] = []

        # 分析行为倾向
        # 检查协作关键词
        cooperation_count = sum(1 for kw in COOPERATIVE_KEYWORDS if kw in content)
        # 检查自私关键词
        selfish_count = sum(1 for kw in SELFISH_KEYWORDS if kw in content)

        # 计算行为影响
        if cooperation_count > selfish_count:
            # 协作行为
            impact = 0.1 * cooperation_count  # 每多一个协作关键词增加正面影响
            impact = min(impact, 0.5)  # 最高0.5
            result["impact"] = impact
            result["behavior"] = "cooperative"
            result["feedback"] = f"协作行为，影响力+{impact:.2f}"
            self.cooperation_score += impact
            self.deaths_prevented += int(impact * 10)
            self.economic_loss_reduced += impact * 5
        elif selfish_count > cooperation_count:
            # 自私行为
            impact = -0.1 * selfish_count  # 每多一个自私关键词增加负面影响
            impact = max(impact, -0.5)  # 最低-0.5
            result["impact"] = impact
            result["behavior"] = "selfish"
            result["feedback"] = f"自私行为，影响力{impact:.2f}"
            self.selfish_score += abs(impact)
        else:
            # 中性或未明确的行为
            result["impact"] = 0.0
            result["behavior"] = "neutral"
            result["feedback"] = "中性行为，无明显影响"

        # 记录agent的行为
        self.agent_actions[agent.id].append({
            "type": action_type,
            "content": content,
            "impact": result["impact"],
            "behavior": result["behavior"]
        })

        # 更新agent记忆
        memory_text = f"在{self.emergency_type}事件中，我表现出{'协作' if result['behavior'] == 'cooperative' else '自私' if result['behavior'] == 'selfish' else '中性'}行为：{content[:50]}..."
        if hasattr(agent, "add_memory"):
            agent.add_memory(memory_text)

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
        self.remaining_duration -= 1

        step_result = {
            "step": step,
            "emergency": self.emergency_type,
            "remaining_duration": self.remaining_duration,
            "severity": self.severity,
            "agent_responses": [],
            "environmental_impact": {},
        }

        # 计算协作对事件的缓解效果
        cooperation_factor = self.cooperation_score / max(len(agents), 1) * 0.1
        selfish_factor = self.selfish_score / max(len(agents), 1) * 0.1

        # 更新严重程度（协作减少，自私增加）
        self.severity = max(0.1, min(1.0,
            self.severity - cooperation_factor + selfish_factor * 0.5
        ))

        # 更新健康和财富状态
        self._apply_environmental_impact(agents)

        # 记录本轮行为
        for agent_id, actions in self.agent_actions.items():
            if actions:
                last_action = actions[-1]
                agent_name = agents.get(agent_id, None)
                name = getattr(agent_name, "name", agent_id) if agent_name else agent_id
                step_result["agent_responses"].append({
                    "agent": name,
                    "behavior": last_action["behavior"],
                    "impact": last_action["impact"]
                })

        # 记录环境变化
        step_result["environmental_impact"] = {
            "health_change": self.current_health - self.initial_health,
            "wealth_change": self.current_wealth - self.initial_wealth,
            "current_severity": self.severity,
            "deaths_prevented_cumulative": self.deaths_prevented,
            "economic_loss_reduced_cumulative": f"{min(self.economic_loss_reduced, 30):.1f}%"
        }

        # 添加事件记录
        self.add_event({
            "type": "emergency_step",
            "round": step,
            "remaining_duration": self.remaining_duration,
            "severity": self.severity,
            "cooperation_score": self.cooperation_score,
            "selfish_score": self.selfish_score
        })

        # 检查是否结束
        if self.remaining_duration <= 0:
            self._complete_scenario(agents)
        else:
            # 每3轮进行一次事件阶段变化
            if step % 3 == 0 and step > 0:
                self._progress_emergency_phase(step_result)

        return step_result

    def _apply_environmental_impact(self, agents: Dict[str, Any]) -> None:
        """应用环境对智能体的影响

        Args:
            agents: 智能体字典
        """
        # 计算本轮的自然影响（基于严重程度）
        natural_health_impact = -self.severity * 0.05 * self.impact_range
        natural_wealth_impact = -self.severity * 0.08 * self.impact_range

        for agent in agents.values():
            if not hasattr(agent, "wealth"):
                continue

            # 协作行为可以抵消部分负面影响
            agent_cooperation = 0.0
            if agent.id in self.agent_actions:
                for action in self.agent_actions[agent.id]:
                    if action["behavior"] == "cooperative":
                        agent_cooperation += action["impact"]

            # 计算最终影响
            health_change = natural_health_impact + agent_cooperation * 0.1
            wealth_change = natural_wealth_impact + agent_cooperation * 0.15

            # 应用到agent
            if hasattr(agent, "wealth"):
                # 健康
                current_health = agent.wealth.get("health", 0.5)
                new_health = max(-1.0, min(1.0, current_health + health_change))
                agent.wealth["health"] = round(new_health, 3)

                # 财富（金钱）
                current_money = agent.wealth.get("money", 10000)
                money_change = wealth_change * 5000  # 转换为金钱
                new_money = max(0, current_money + money_change)
                agent.wealth["money"] = round(new_money, 2)

            # 更新心情（负面事件影响心情）
            if hasattr(agent, "update_mood"):
                mood_impact = -self.severity * 0.1
                if agent_cooperation > 0:
                    mood_impact += agent_cooperation * 0.05
                agent.update_mood('emergency', mood_impact, f"应对{self.emergency_type}事件")

            # 检查是否死亡（健康极低）
            if hasattr(agent, "wealth"):
                if agent.wealth.get("health", 0.5) < -0.8:
                    self.total_deaths += 1
                    agent.status = "死亡"

        # 更新全局状态
        self.current_health += natural_health_impact
        self.current_wealth += natural_wealth_impact

        # 累计经济损失
        self.economic_losses = (1.0 - self.current_wealth) * 100

    def _progress_emergency_phase(self, step_result: Dict[str, Any]) -> None:
        """推进事件阶段

        Args:
            step_result: 步进结果
        """
        phase_names = {
            "earthquake": ["初震", "余震期", "救援期", "重建期"],
            "economic_crisis": ["危机爆发", "市场动荡", "衰退期", "复苏期"],
            "pandemic": ["疫情爆发", "扩散期", "高峰期", "控制期", "平息期"],
            "flood": ["洪水预警", "洪峰来临", "紧急救援", "退水期", "重建期"]
        }

        phases = phase_names.get(self.emergency_type, ["初期", "中期", "后期", "结束"])
        current_phase_idx = len(phases) - 1 - (self.remaining_duration // 2)
        current_phase_idx = max(0, min(current_phase_idx, len(phases) - 1))
        current_phase = phases[current_phase_idx]

        step_result["phase"] = current_phase
        self.data["current_phase"] = current_phase

        self.add_event({
            "type": "emergency_phase",
            "phase": current_phase,
            "severity": self.severity
        })

    def _complete_scenario(self, agents: Dict[str, Any]) -> None:
        """完成场景，生成最终报告

        Args:
            agents: 智能体字典
        """
        # 计算最终统计
        total_agents = len(agents)
        surviving_agents = sum(1 for a in agents.values()
                             if getattr(a, "status", "") != "死亡")

        # 计算协作效果
        avg_cooperation = self.cooperation_score / max(total_agents, 1)
        avg_selfish = self.selfish_score / max(total_agents, 1)

        # 协作挽救生命的计算
        deaths_prevented = int(avg_cooperation * 100)
        economic_loss_reduced = min(avg_cooperation * 30, 30.0)

        # 生成报告
        emergency_names = {
            "earthquake": "强烈地震",
            "economic_crisis": "经济危机",
            "pandemic": "疫情爆发",
            "flood": "洪涝灾害"
        }
        emergency_name = emergency_names.get(self.emergency_type, self.emergency_type)

        # 协作/自私比例
        total_behavior_score = self.cooperation_score + self.selfish_score
        if total_behavior_score > 0:
            cooperation_ratio = self.cooperation_score / total_behavior_score
        else:
            cooperation_ratio = 0.5  # 默认中性

        # 生成总结
        if cooperation_ratio > 0.6:
            summary = f"在{emergency_name}中，社区表现出色！通过互助协作，成功挽救了约{deaths_prevented}条生命，减少了约{economic_loss_reduced:.0f}%的经济损失。社区的团结精神令人敬佩。"
        elif cooperation_ratio > 0.4:
            summary = f"面对{emergency_name}，社区表现一般。虽然有一些协作行为，但效果有限。共挽救了约{deaths_prevented}条生命，减少了约{economic_loss_reduced:.0f}%的经济损失。仍有提升空间。"
        else:
            summary = f"在{emergency_name}中，社区表现不佳。自私行为较多，导致损失加剧。仅有约{deaths_prevented}条生命被挽救，经济损失减少不足{economic_loss_reduced:.0f}%。这次事件暴露了社区凝聚力不足的问题。"

        # 构建最终报告
        final_report = {
            "deaths_prevented": deaths_prevented,
            "economic_loss_reduced": f"{economic_loss_reduced:.0f}%",
            "survival_rate": f"{(surviving_agents / max(total_agents, 1)) * 100:.1f}%",
            "cooperation_score": round(self.cooperation_score, 2),
            "selfish_score": round(self.selfish_score, 2),
            "total_deaths": self.total_deaths,
            "summary": summary,
            "emergency_type": self.emergency_type,
            "severity": self.severity,
            "duration": self.duration,
            "surviving_agents": surviving_agents,
            "total_agents": total_agents
        }

        # 更新结果
        self.result["summary"] = summary
        self.data["final_report"] = final_report

        self.add_event({
            "type": "emergency_end",
            "report": final_report
        })

        self.set_completed(summary)

    def get_summary(self) -> Dict[str, Any]:
        """获取场景总结

        Returns:
            Dict[str, Any]: 场景总结
        """
        base_summary = super().get_summary()

        # 添加突发事件特有的统计数据
        base_summary.update({
            "emergency_type": self.emergency_type,
            "severity": self.severity,
            "duration": self.duration,
            "cooperation_score": self.cooperation_score,
            "selfish_score": self.selfish_score,
            "deaths_prevented": self.deaths_prevented,
            "economic_loss_reduced": self.economic_loss_reduced,
            "total_deaths": self.total_deaths,
        })

        # 添加最终报告
        if "final_report" in self.data:
            base_summary["final_report"] = self.data["final_report"]

        return base_summary

    def get_cooperation_report(self) -> Dict[str, Any]:
        """获取协作报告（详细分析每个Agent的行为）

        Returns:
            Dict[str, Any]: 协作报告
        """
        agent_reports = []

        for agent_id, actions in self.agent_actions.items():
            if not actions:
                continue

            total_impact = sum(a["impact"] for a in actions)
            behaviors = [a["behavior"] for a in actions]
            cooperative_count = behaviors.count("cooperative")
            selfish_count = behaviors.count("selfish")

            agent_reports.append({
                "agent_id": agent_id,
                "total_actions": len(actions),
                "cooperative_actions": cooperative_count,
                "selfish_actions": selfish_count,
                "total_impact": round(total_impact, 3),
                "final_behavior": "cooperative" if cooperative_count > selfish_count else "selfish" if selfish_count > cooperative_count else "neutral"
            })

        return {
            "total_agents_acted": len(agent_reports),
            "overall_cooperation_score": round(self.cooperation_score, 2),
            "overall_selfish_score": round(self.selfish_score, 2),
            "agent_reports": agent_reports,
            "deaths_prevented": self.deaths_prevented,
            "economic_loss_reduced": f"{min(self.economic_loss_reduced, 30):.1f}%"
        }
