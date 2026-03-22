"""
Simulation Engine - 模拟引擎核心

负责管理场景生命周期、协调智能体与环境交互、处理时间步进和事件分发。
"""

import time
import threading
from typing import Dict, List, Optional, Any, Type
from abc import ABC

from simulation.base import BaseAgent, BaseEnvironment, BaseEntity
from simulation.scenarios.base import BaseScenario


class SimulationEngine:
    """模拟引擎

    核心组件，负责：
    - 管理场景生命周期
    - 协调智能体与环境交互
    - 处理时间步进和事件分发
    """

    def __init__(
        self,
        scenario: BaseScenario,
        environment: Optional[BaseEnvironment] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化模拟引擎

        Args:
            scenario: 场景实例
            environment: 环境实例（可选）
            config: 配置字典
        """
        self.scenario = scenario
        self.environment = environment
        self.config = config or {}

        # 智能体管理
        self.agents: Dict[str, BaseAgent] = {}

        # 模拟状态
        self.is_running = False
        self.current_step = 0
        self.total_steps = 0

        # 线程安全
        self.lock = threading.Lock()

        # 回调函数
        self.on_step_start: Optional[callable] = None
        self.on_step_end: Optional[callable] = None
        self.on_simulation_end: Optional[callable] = None

    def add_agent(self, agent: BaseAgent, position: Optional[str] = None) -> bool:
        """添加智能体

        Args:
            agent: 智能体实例
            position: 初始位置（可选）

        Returns:
            bool: 是否添加成功
        """
        with self.lock:
            if agent.id in self.agents:
                return False

            self.agents[agent.id] = agent

            # 如果有环境，添加到环境中
            if self.environment:
                self.environment.add_entity(agent, position)

            return True

    def remove_agent(self, agent_id: str) -> bool:
        """移除智能体

        Args:
            agent_id: 智能体ID

        Returns:
            bool: 是否移除成功
        """
        with self.lock:
            if agent_id not in self.agents:
                return False

            agent = self.agents.pop(agent_id)

            # 如果有环境，从环境中移除
            if self.environment:
                self.environment.remove_entity(agent_id)

            return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体

        Args:
            agent_id: 智能体ID

        Returns:
            Optional[BaseAgent]: 智能体实例
        """
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[BaseAgent]:
        """获取所有智能体

        Returns:
            List[BaseAgent]: 智能体列表
        """
        return list(self.agents.values())

    def setup(self) -> None:
        """初始化场景

        调用场景的 setup 方法进行初始化
        """
        # 将环境传递给场景
        self.scenario.environment = self.environment

        # 设置智能体
        for agent in self.agents.values():
            self.scenario.setup_agent(agent)

        # 调用场景的 setup
        self.scenario.setup()

    def step(self) -> Dict[str, Any]:
        """执行一步模拟

        Returns:
            Dict[str, Any]: 步进结果
        """
        if not self.is_running:
            return {"error": "Simulation not running"}

        with self.lock:
            self.current_step += 1

            # 触发步进开始回调
            if self.on_step_start:
                self.on_step_start(self.current_step)

            # 让场景处理这一步
            step_result = self.scenario.step(
                agents=self.agents,
                environment=self.environment,
                step=self.current_step
            )

            # 如果有环境，推进时间
            if self.environment:
                self.environment.tick()

            # 触发步进结束回调
            if self.on_step_end:
                self.on_step_end(self.current_step, step_result)

            return step_result

    def get_scenario_info(self) -> Dict[str, Any]:
        """获取场景信息

        Returns:
            Dict[str, Any]: 场景信息字典
        """
        if hasattr(self.scenario, 'get_scenario_info'):
            return self.scenario.get_scenario_info()
        return {
            "name": getattr(self.scenario, 'name', '未知场景'),
            "description": getattr(self.scenario, 'description', ''),
            "type": "dialogue",
            "goals": [],
            "era": "default",
            "max_rounds": 10,
            "events": [],
            "agents": []
        }

    def run(self, steps: Optional[int] = None) -> Dict[str, Any]:
        """运行模拟

        Args:
            steps: 运行步数（可选，默认使用场景配置）

        Returns:
            Dict[str, Any]: 模拟结果
        """
        self.is_running = True

        # 确定运行步数
        if steps is None:
            steps = self.config.get("default_steps", 10)
        self.total_steps = steps

        # 初始化
        print("正在初始化场景...")
        self.setup()
        print("场景初始化完成")

        # 运行模拟循环
        for step in range(steps):
            if not self.is_running:
                break

            print(f"执行第 {step + 1} 步...")
            result = self.step()
            print(f"第 {step + 1} 步完成")

            # 检查场景是否完成
            if self.scenario.is_complete():
                print(f"场景在第 {step + 1} 步完成")
                break

        # 模拟结束
        self.is_running = False

        # 触发结束回调
        if self.on_simulation_end:
            self.on_simulation_end()

        # 返回场景总结
        return self.scenario.get_summary()

    def stop(self) -> None:
        """停止模拟"""
        self.is_running = False

    def pause(self) -> None:
        """暂停模拟"""
        self.is_running = False

    def resume(self) -> None:
        """恢复模拟"""
        self.is_running = True

    def get_status(self) -> Dict[str, Any]:
        """获取模拟状态

        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "is_running": self.is_running,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "agent_count": len(self.agents),
            "scenario_complete": self.scenario.is_complete() if self.scenario else False
        }
