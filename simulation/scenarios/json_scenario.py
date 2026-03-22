"""
JSON Scenario - 基于JSON配置的场景执行引擎

允许通过JSON文件定义场景、任务和智能体行为。

JSON Schema:
{
    "name": "场景名称",
    "description": "场景描述",
    "type": "dialogue|debate|emergency|roleplay",
    "goals": ["目标1", "目标2"],
    "config": {
        "max_rounds": 10,
        "max_participants": 5
    },
    "agents": [
        {
            "id": "agent1",
            "name": "角色名",
            "role": "角色描述",
            "personality": "性格描述",
            "goals": ["个人目标1"],
            "prompt_template": "可选，自定义prompt"
        }
    ],
    "events": [
        {
            "trigger": {"type": "round", "value": 3},
            "type": "dialogue",
            "content": "事件内容",
            "participants": ["agent1", "agent2"]
        }
    ],
    "evaluation": {
        "type": "cooperation|competition|goal_achievement",
        "criteria": [
            {"metric": "cooperation_score", "weight": 0.5},
            {"metric": "goal_achievement", "weight": 0.5}
        ]
    },
    "results": {
        "summary_template": "总结模板"
    }
}

用法:
    python main.py --scenario json --scenario-file scenarios/my_scenario.json
"""

import json
import os
import random
import threading
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from simulation.scenarios.base import BaseScenario


class JSONScenario(BaseScenario):
    """JSON定义场景的执行器"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        # JSON配置
        self.scenario_file = config.get("scenario_file") if config else None
        self.scenario_data = None

        # 执行状态
        self.current_round = 0
        self.agent_configs = []  # JSON中定义的智能体配置
        self.event_queue = []  # 待触发的事件
        self.triggered_events = set()  # 已触发的事件索引

        # 锁
        self.lock = threading.Lock()

        # 评估数据
        self.evaluation_data = {
            "cooperation_count": 0,
            "conflict_count": 0,
            "goals_achieved": {},
            "dialogue_count": 0,
            "round_scores": []
        }

        # 加载JSON配置
        if self.scenario_file:
            self._load_scenario(self.scenario_file)

    def _load_scenario(self, file_path: str):
        """加载JSON场景文件"""
        if not os.path.exists(file_path):
            # 尝试在scenarios目录下查找
            file_path = os.path.join("simulation/scenarios", file_path)
            if not os.path.exists(file_path):
                file_path = os.path.join("scenarios", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"场景文件不存在: {self.scenario_file}")

        with open(file_path, 'r', encoding='utf-8') as f:
            self.scenario_data = json.load(f)

        self.name = self.scenario_data.get("name", "未命名场景")
        self.description = self.scenario_data.get("description", "")

        # 加载智能体配置
        self.agent_configs = self.scenario_data.get("agents", [])

        # 加载事件配置
        self.events = self.scenario_data.get("events", [])

        # 加载评估配置
        self.evaluation = self.scenario_data.get("evaluation", {})

        # 加载结果配置
        self.results_config = self.scenario_data.get("results", {})

        print(f"加载场景: {self.name}")
        print(f"描述: {self.description}")
        print(f"智能体数: {len(self.agent_configs)}")
        print(f"事件数: {len(self.events)}")

    def setup(self) -> None:
        """初始化场景"""
        self.is_initialized = True
        self.current_round = 0

        # 初始化评估数据
        self.evaluation_data = {
            "cooperation_count": 0,
            "conflict_count": 0,
            "goals_achieved": {},
            "dialogue_count": 0,
            "round_scores": []
        }

        # 初始化事件队列
        self.event_queue = []
        self.triggered_events = set()

        print(f"\n=== {self.name} 开始 ===")

    def setup_agent(self, agent) -> None:
        """设置智能体

        Args:
            agent: 智能体实例
        """
        # 查找该智能体的JSON配置
        agent_config = None
        for cfg in self.agent_configs:
            if cfg.get("id") == agent.id or cfg.get("name") == agent.name:
                agent_config = cfg
                break

        # 如果没有配置，分配一个默认配置
        if not agent_config and self.agent_configs:
            agent_config = random.choice(self.agent_configs)

        if agent_config:
            # 存储配置到智能体
            agent.scenario_role = agent_config.get("role", "")
            agent.scenario_goals = agent_config.get("goals", [])
            agent.scenario_prompt_template = agent_config.get("prompt_template", "")

            print(f"  {agent.name} 扮演: {agent.scenario_role}")

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

        # 构建基础prompt
        prompt_parts = []

        # 添加场景描述
        if self.description:
            prompt_parts.append(f"【场景】{self.description}")

        # 添加角色描述
        if hasattr(agent, 'scenario_role') and agent.scenario_role:
            prompt_parts.append(f"【你的角色】{agent.scenario_role}")

        # 添加目标
        if hasattr(agent, 'scenario_goals') and agent.scenario_goals:
            goals_str = "、".join(agent.scenario_goals)
            prompt_parts.append(f"【你的目标】{goals_str}")

        # 添加当前情境
        prompt_parts.append(f"【当前位置】{location}")
        if others:
            others_str = "、".join([a.name for a in others])
            prompt_parts.append(f"【在场人物】{others_str}")

        # 添加自定义prompt模板
        if hasattr(agent, 'scenario_prompt_template') and agent.scenario_prompt_template:
            prompt_parts.append(f"【行为指引】{agent.scenario_prompt_template}")

        # 添加场景类型的行为指导
        scenario_type = self.scenario_data.get("type", "dialogue")
        prompt_parts.append(f"【场景类型】{_get_type_guidance(scenario_type)}")

        # 添加轮次信息
        prompt_parts.append(f"【当前轮次】{self.current_round}/{self.config.get('max_rounds', 10)}")

        return "\n".join(prompt_parts)

    def evaluate_action(self, agent, action: Dict[str, Any]) -> Dict[str, Any]:
        """评估智能体的行动

        Args:
            agent: 智能体实例
            action: 行动字典

        Returns:
            Dict[str, Any]: 评估结果
        """
        action_type = action.get("type", "dialogue")
        content = action.get("content", "")
        score = 0.5
        reason = ""

        # 根据场景类型评估
        scenario_type = self.scenario_data.get("type", "dialogue")

        if scenario_type == "debate":
            score, reason = self._evaluate_debate_action(agent, action, content)
        elif scenario_type == "cooperation":
            score, reason = self._evaluate_cooperation_action(agent, action, content)
        elif scenario_type == "emergency":
            score, reason = self._evaluate_emergency_action(agent, action, content)
        else:
            score, reason = self._evaluate_dialogue_action(agent, action, content)

        # 更新评估数据
        self.evaluation_data["dialogue_count"] += 1
        self.evaluation_data["round_scores"].append(score)

        if "合作" in reason or "协作" in reason:
            self.evaluation_data["cooperation_count"] += 1
        elif "冲突" in reason or "对抗" in reason:
            self.evaluation_data["conflict_count"] += 1

        return {"score": score, "reason": reason}

    def _evaluate_dialogue_action(self, agent, action: str, content: str) -> tuple:
        """评估对话行动"""
        score = 0.5
        reason = "正常对话"

        # 检查是否有实质内容
        if len(content) < 5:
            score = 0.3
            reason = "对话内容过短"
        elif len(content) > 200:
            score = 0.6
            reason = "对话内容丰富"

        # 检查是否有角色扮演
        if hasattr(agent, 'scenario_role'):
            score += 0.1
            reason += "，符合角色设定"

        return score, reason

    def _evaluate_debate_action(self, agent, action: Dict, content: str) -> tuple:
        """评估辩论行动"""
        score = 0.5
        reason = "正常发言"

        # 辩论关键词
        positive_words = ["我认为", "我的观点", "论证", "理由", "支持", "反对"]
        negative_words = ["你错了", "胡说", "无语", "滚"]

        has_opinion = any(word in content for word in positive_words)
        is_hostile = any(word in content for word in negative_words)

        if has_opinion:
            score += 0.2
            reason = "观点明确"

        if is_hostile:
            score -= 0.2
            reason = "攻击性言论"

        return max(0, min(1, score)), reason

    def _evaluate_cooperation_action(self, agent, action: Dict, content: str) -> tuple:
        """评估合作行动"""
        score = 0.5
        reason = "正常互动"

        cooperation_words = ["我们", "一起", "合作", "协助", "共同", "团队"]
        self_words = ["我", "我的", "自己"]

        has_cooperation = any(word in content for word in cooperation_words)
        has_selfish = any(word in content for word in self_words) and "我们" not in content

        if has_cooperation:
            score += 0.3
            reason = "展现合作精神"
        elif has_selfish:
            score -= 0.1
            reason = "略显自私"

        return max(0, min(1, score)), reason

    def _evaluate_emergency_action(self, agent, action: Dict, content: str) -> tuple:
        """评估紧急情况行动"""
        score = 0.5
        reason = "正常反应"

        heroic_words = ["帮助", "救援", "一起", "我们", "共同", "协助"]
        coward_words = ["逃跑", "离开", "不管", "自己"]

        has_heroic = any(word in content for word in heroic_words)
        has_coward = any(word in content for word in coward_words)

        if has_heroic:
            score += 0.3
            reason = "勇敢相助"
        elif has_coward:
            score -= 0.2
            reason = "逃避责任"

        return max(0, min(1, score)), reason

    def step(self, agents: Dict[str, Any], environment: Any, step: int) -> Dict[str, Any]:
        """执行一步模拟

        Args:
            agents: 智能体字典
            environment: 环境实例
            step: 当前步数

        Returns:
            Dict[str, Any]: 步进结果
        """
        self.current_round = step

        # 检查并触发事件
        self._check_and_trigger_events(step, agents)

        # 处理事件队列
        events_processed = []
        while self.event_queue:
            event = self.event_queue.pop(0)
            events_processed.append(event)

        # 计算本轮得分
        round_score = sum(self.evaluation_data["round_scores"][-len(agents):]) / max(1, len(agents))

        # 检查是否完成
        max_rounds = self.config.get("max_rounds", 10)
        if step >= max_rounds:
            self.set_completed()

        return {
            "step": step,
            "round_score": round_score,
            "events_processed": len(events_processed),
            "total_cooperation": self.evaluation_data["cooperation_count"],
            "total_conflict": self.evaluation_data["conflict_count"]
        }

    def _check_and_trigger_events(self, step: int, agents: Dict[str, Any]):
        """检查并触发事件"""
        for i, event in enumerate(self.events):
            if i in self.triggered_events:
                continue

            trigger = event.get("trigger", {})
            trigger_type = trigger.get("type")

            # 检查触发条件
            should_trigger = False

            if trigger_type == "round" and step == trigger.get("value"):
                should_trigger = True
            elif trigger_type == "round_after" and step > trigger.get("value"):
                should_trigger = True
            elif trigger_type == "percentage" and len(agents) > 0:
                progress = len(self.evaluation_data["round_scores"]) / len(agents)
                if progress >= trigger.get("value", 1.0):
                    should_trigger = True

            if should_trigger:
                self.triggered_events.add(i)
                self.event_queue.append(event)
                print(f"  [事件触发] {event.get('content', event.get('description', '未命名事件'))}")

    def is_complete(self) -> bool:
        """判断场景是否完成"""
        return self.is_completed

    def get_summary(self) -> Dict[str, Any]:
        """获取场景总结

        Returns:
            Dict[str, Any]: 场景总结
        """
        # 计算最终得分
        final_score = sum(self.evaluation_data["round_scores"]) / max(1, len(self.evaluation_data["round_scores"]))

        # 生成总结
        summary_template = self.results_config.get("summary_template",
            "场景完成。合作次数: {cooperation}, 冲突次数: {conflict}, 最终得分: {score:.2f}")

        summary = summary_template.format(
            name=self.name,
            cooperation=self.evaluation_data["cooperation_count"],
            conflict=self.evaluation_data["conflict_count"],
            score=final_score
        )

        return {
            "name": self.name,
            "description": self.description,
            "total_rounds": self.current_round,
            "evaluation": self.evaluation_data,
            "final_score": final_score,
            "summary": summary,
            "type": self.scenario_data.get("type", "dialogue"),
            "goals_achieved": self.evaluation_data.get("goals_achieved", {})
        }


def _get_type_guidance(scenario_type: str) -> str:
    """获取场景类型的行为指导"""
    guidance = {
        "dialogue": "自由对话，展现你的性格和智慧。",
        "debate": "围绕主题展开辩论，提出有力论点，注意逻辑和证据。",
        "cooperation": "与其他智能体协作，共同完成任务或达成目标。",
        "emergency": "面对紧急情况，做出勇敢和负责任的决定。",
        "roleplay": "完全代入角色，按照角色设定的方式思考和行动。",
        "negotiation": "通过对话和协商，达成双方都能接受的协议。"
    }
    return guidance.get(scenario_type, "根据场景要求行动。")


# JSON场景注册
def load_json_scenario(file_path: str, config: Dict[str, Any] = None) -> JSONScenario:
    """加载JSON场景文件"""
    if config is None:
        config = {}
    config["scenario_file"] = file_path
    return JSONScenario(config)
