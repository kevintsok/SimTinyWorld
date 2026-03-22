"""
UI Main Entry Point - UI主入口

启动游戏风格可视化界面。
使用新的模块化UI：MainView（主界面）和 ScenarioView（场景视图）。
支持多Session管理。
"""

import pygame
import sys
import os
import argparse
import time
import random
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.main_view import MainView, MainViewInterface
from ui.scenario_view import ScenarioView, ScenarioViewInterface
from ui.session_panel import SessionPanel, SessionPanelInterface
from environment.world import World
from environment.layout import EnvironmentLayout
from agent.base_agent import BaseAgent
from session import SessionManager
from simulation.scenarios.daily_life import DailyLifeScenario


class SimulationController:
    """模拟UI主控制器

    集成MainView（主界面）和ScenarioView（场景视图），
    管理两者之间的切换和数据流动。支持多Session管理。
    """

    def __init__(self, width: int = 1000, height: int = 700, fast_mode: bool = False):
        """初始化UI

        Args:
            width: 窗口宽度
            height: 窗口高度
            fast_mode: 是否使用快速模式（不调用LLM）
        """
        pygame.init()
        self.width = width
        self.height = height
        self.fast_mode = fast_mode

        # 创建窗口（两个视图共享）
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("多智能体社会模拟")

        # Session管理器
        self.session_manager = SessionManager()
        self.current_session_id: Optional[str] = None
        self.current_session_name: str = "未命名Session"

        # 创建主视图（带回调接口）
        main_interface = MainViewInterface(
            on_scenario_selected=self._on_scenario_selected,
            on_agent_created=self._on_agent_created,
            on_agent_imported=self._on_agent_imported,
            on_quick_start=self._on_quick_start,
            on_session_clicked=self._on_session_clicked
        )
        self.main_view = MainView(self.screen, pygame.Rect(0, 0, width, height), main_interface)

        # 创建场景视图（带回调接口，使用共享的screen）
        scenario_interface = ScenarioViewInterface(
            on_agent_selected=self._on_agent_selected,
            on_agent_detail_toggle=self._on_agent_detail_toggle,
            on_return_to_menu=self._on_return_to_menu,
            on_simulation_control=self._on_simulation_control,
            on_save_session=self._on_save_session_in_scenario,
            on_load_session=self._on_load_session_in_scenario
        )
        self.scenario_view = ScenarioView(width, height, scenario_interface, self.screen)

        # 创建Session面板（带回调接口）
        session_interface = SessionPanelInterface(
            on_continue_session=self._on_continue_session,
            on_save_session=self._on_save_session,
            on_delete_session=self._on_delete_session,
            on_new_session=self._on_new_session,
            on_load_session=self._on_load_session
        )
        self.session_panel = SessionPanel(
            self.screen,
            pygame.Rect(width // 4, height // 6, width // 2, height // 2),
            self.session_manager,
            session_interface
        )
        self.session_panel.visible = False

        # 状态
        self.current_view = "main"  # main, scenario
        self.is_paused = True
        self.speed = 1.0
        self.selected_agent_id: Optional[str] = None

        # 模拟数据
        self.agents: Dict[str, BaseAgent] = {}
        self.name_to_id: Dict[str, str] = {}  # 名字到ID的快速映射
        self.world: Optional[World] = None
        self.custom_agents: List[Dict] = []  # 用户创建的智能体

        # 时钟
        self.clock = pygame.time.Clock()

        # 模拟步进计时
        self.last_step_time = 0
        self.step_interval = 2.0  # 秒

        # 每日交互轮数状态
        self.current_day = 1
        self.interact_rounds_per_day = 5  # 默认每日5轮交互
        self.current_interact_round = 0
        self.total_dialogue_count = 0  # 累计对话次数（每个智能体参与一次对话计1）

        # 当前场景类型
        self.scenario_type = "daily_life"

        # DailyLifeScenario实例
        self.scenario: Optional[DailyLifeScenario] = None

        # 模拟步数计数器
        self.current_step = 0

    # ==================== 回调处理 ====================

    def _on_scenario_selected(self, scenario_id: str, config: dict):
        """场景被选中"""
        print(f"场景选中: {scenario_id}, 配置: {config}")

    def _on_agent_created(self, agent_data: dict):
        """创建智能体"""
        self.custom_agents.append(agent_data)
        print(f"智能体创建: {agent_data.get('name')}")

    def _on_agent_imported(self, agent_data: dict):
        """导入智能体"""
        print(f"智能体导入: {agent_data}")

    def _on_quick_start(self, config: dict):
        """快速开始"""
        self._start_simulation(config)

    def _on_session_clicked(self):
        """Session按钮点击"""
        self.session_panel.refresh_sessions()
        self.session_panel.visible = True

    def _on_continue_session(self, session_id: str):
        """继续选中的Session"""
        self.session_panel.visible = False
        self._load_session(session_id)

    def _on_save_session(self, session_id: str):
        """保存Session"""
        self._save_current_session(session_id)

    MAX_NOTIFICATIONS = 50  # 限制最大通知数量

    def _add_notification(self, content: str, duration: float = 2.5):
        """添加通知到场景视图"""
        if self.current_view == "scenario" and hasattr(self, 'scenario_view'):
            # 清理已过期的通知
            now = time.time()
            self.scenario_view.event_notifications = [
                n for n in self.scenario_view.event_notifications
                if now - n["start_time"] < n["duration"]
            ]
            # 限制最大数量
            if len(self.scenario_view.event_notifications) >= self.MAX_NOTIFICATIONS:
                self.scenario_view.event_notifications = self.scenario_view.event_notifications[-self.MAX_NOTIFICATIONS:]
            self.scenario_view.event_notifications.append({
                "content": content,
                "start_time": time.time(),
                "duration": duration
            })

    def _on_delete_session(self, session_id: str):
        """删除Session"""
        if self.session_manager.delete_session(session_id):
            print(f"Session {session_id} 已删除")
            self.session_panel.refresh_sessions()
            if self.selected_agent_id == session_id:
                self.selected_agent_id = None

    def _on_new_session(self, name: str):
        """创建新Session"""
        session_id = self.session_manager.create_session(
            name=name,
            description="",
            scenario_type=self.scenario_type
        )
        self.current_session_id = session_id
        self.current_session_name = name
        self.session_panel.refresh_sessions()
        print(f"创建新Session: {name} ({session_id})")

    def _on_load_session(self, session_id: str):
        """加载Session"""
        self.session_panel.visible = False
        self._load_session(session_id)

    def _on_agent_selected(self, agent_id: str):
        """智能体被选中"""
        self.selected_agent_id = agent_id
        print(f"智能体选中: {agent_id}")

    def _on_agent_detail_toggle(self, visible: bool):
        """详情显示状态变化"""
        print(f"详情显示: {visible}")

    # ==================== Session管理 ====================

    def to_dict(self) -> Dict[str, Any]:
        """将UI状态序列化为字典

        Returns:
            Dict: 包含UI状态的字典
        """
        return {
            "current_view": self.current_view,
            "current_day": self.current_day,
            "interact_rounds_per_day": self.interact_rounds_per_day,
            "current_interact_round": self.current_interact_round,
            "total_dialogue_count": self.total_dialogue_count,
            "is_paused": self.is_paused,
            "speed": self.speed,
            "selected_agent_id": self.selected_agent_id,
            "custom_agents": self.custom_agents,
            "scenario_type": self.scenario_type,
            "current_session_id": self.current_session_id,
            "current_session_name": self.current_session_name,
        }

    def from_dict(self, data: Dict[str, Any]):
        """从字典恢复UI状态

        Args:
            data: 包含UI状态的字典
        """
        self.current_view = data.get("current_view", "main")
        self.current_day = data.get("current_day", 1)
        self.interact_rounds_per_day = data.get("interact_rounds_per_day", 5)
        self.current_interact_round = data.get("current_interact_round", 0)
        self.total_dialogue_count = data.get("total_dialogue_count", 0)
        self.is_paused = data.get("is_paused", True)
        self.speed = data.get("speed", 1.0)
        self.selected_agent_id = data.get("selected_agent_id")
        self.custom_agents = data.get("custom_agents", [])
        self.scenario_type = data.get("scenario_type", "daily_life")
        self.current_session_id = data.get("current_session_id")
        self.current_session_name = data.get("current_session_name", "未命名Session")

    def save_current_session(self) -> bool:
        """保存当前Session（供外部调用）

        Returns:
            bool: 是否保存成功
        """
        if not self.current_session_id:
            # 如果没有当前session，创建一个
            self.current_session_id = self.session_manager.create_session(
                name=self.current_session_name,
                description="",
                scenario_type=self.scenario_type
            )

        return self._save_current_session(self.current_session_id)

    def _save_current_session(self, session_id: str) -> bool:
        """保存指定Session

        Args:
            session_id: Session ID

        Returns:
            bool: 是否保存成功
        """
        # 获取各组件状态
        engine_state = {}  # TODO: 集成SimulationEngine时填充
        world_state = self.world.to_dict() if self.world else {}
        scenario_state = self.scenario_view.to_dict()
        controller_state = self.to_dict()

        # 获取智能体数据
        agents_data = {}
        for agent_id, agent in self.agents.items():
            agents_data[agent_id] = agent.to_dict()

        success = self.session_manager.save_session(
            session_id=session_id,
            engine_state=engine_state,
            world_state=world_state,
            scenario_state=scenario_state,
            controller_state=controller_state,
            agents_data=agents_data
        )

        if success:
            print(f"Session {session_id} 已保存")
            self._add_notification("✓ Session已保存")
        else:
            print(f"Session {session_id} 保存失败")
            self._add_notification("✗ Session保存失败")

        return success

    def _load_session(self, session_id: str):
        """加载并恢复Session

        Args:
            session_id: Session ID
        """
        session_data = self.session_manager.load_session(session_id)
        if not session_data:
            print(f"无法加载Session {session_id}")
            return

        metadata = session_data.get("metadata")
        state = session_data.get("state", {})
        agents_data = session_data.get("agents", {})

        if not state:
            print(f"Session {session_id} 无有效状态数据")
            return

        # 恢复元数据
        if metadata:
            self.current_session_id = metadata.session_id
            self.current_session_name = metadata.name
            self.scenario_type = metadata.scenario_type

        # 恢复控制器状态
        controller_state = state.get("controller", {})
        self.from_dict(controller_state)

        # 恢复世界状态
        world_state = state.get("world", {})
        if world_state:
            self.world = World.from_dict(world_state)

        # 恢复场景视图状态
        scenario_state = state.get("scenario", {})
        self.scenario_view.from_dict(scenario_state)

        # 恢复智能体
        self.agents.clear()
        self.name_to_id.clear()
        for agent_id, agent_data in agents_data.items():
            agent = BaseAgent.from_dict(agent_data)
            self.agents[agent_id] = agent
            self.name_to_id[agent.name] = agent_id
            if self.world:
                location = agent_data.get("position", "未知")
                self.world.add_agent(agent_id, agent)

        # 更新场景视图
        self._update_scenario_view()

        # 切换到场景视图
        self.current_view = "scenario"
        pygame.display.set_caption(f"多智能体社会模拟 - {self.current_session_name}")

    # ==================== 原有回调 ====================

    def _on_return_to_menu(self):
        """返回主菜单"""
        self.current_view = "main"
        pygame.display.set_caption("多智能体社会模拟")
        print("返回主菜单")

    def _on_simulation_control(self, control_type: str, value: Any):
        """模拟控制"""
        if control_type == "toggle_pause":
            self.is_paused = not self.is_paused
        elif control_type == "speed":
            self.speed = value
        elif control_type == "step":
            self._simulate_step()

    def _on_save_session_in_scenario(self):
        """在仿真场景中保存Session"""
        if self.current_session_id:
            self._save_current_session(self.current_session_id)
        else:
            # 如果没有session_id，创建一个新session
            session_id = self.session_manager.create_session(
                f"Session_{self.current_day}",
                f"第{self.current_day}天自动保存",
                self.scenario_type or "daily_life"
            )
            self.current_session_id = session_id
            self._save_current_session(session_id)

    def _on_load_session_in_scenario(self):
        """在仿真场景中加载Session - 显示Session面板"""
        self.session_panel.visible = True
        self.session_panel.refresh_sessions()

    def _start_simulation(self, config: dict):
        """开始模拟"""
        self.current_view = "scenario"

        # 设置场景类型
        self.scenario_type = config.get("scenario_type", "daily_life")

        # 初始化世界
        location_count = config.get("locations", 5)
        self.world = World(visual_mode=False, location_count=location_count)

        # 初始化DailyLifeScenario
        if self.scenario_type == "daily_life":
            # 创建config字典
            scenario_config = {
                "fast_mode": self.fast_mode,
                "rounds_per_day": config.get("interact_rounds", 5)
            }
            self.scenario = DailyLifeScenario(config=scenario_config)
            # 设置world引用（DailyLifeScenario使用self.world而不是self.environment）
            self.scenario.world = self.world
            self.scenario.setup()
            # 设置每日轮数
            self.scenario.rounds_per_day = config.get("interact_rounds", 5)
        else:
            self.scenario = None

        # 获取位置数据
        locations = {}
        for name, info in self.world.layout.locations.items():
            pos = self.world.layout.positions.get(name, (0, 0))
            locations[name] = {
                "type": info.get("type", "默认"),
                "description": info.get("description", ""),
                "position": pos
            }

        # 获取连接数据
        connections = {}
        for loc_name, loc in self.world.locations.items():
            connections[loc_name] = [
                (conn, self.world.layout.get_distance(loc_name, conn))
                for conn in loc.connected_locations
            ]

        self.scenario_view.set_locations(locations, connections)

        # 设置场景信息
        scenario_type = config.get("scenario_type", "daily_life")
        scenario_name_map = {
            "daily_life": "日常生活",
            "emergency": "突发事件",
            "debate": "观点辩论"
        }
        self.scenario_view.set_scenario_info(
            name=scenario_name_map.get(scenario_type, "智能体模拟"),
            scenario_type=scenario_type
        )

        # 生成智能体
        agent_count = config.get("num_agents", 5)
        custom_agents = config.get("custom_agents", [])

        # 如果有自定义智能体，先添加它们
        for agent_data in custom_agents:
            self._create_agent_from_data(agent_data)

        # 如果智能体数量不足，随机生成
        existing_count = len(self.agents)
        for i in range(agent_count - existing_count):
            self._create_random_agent(f"agent_{i+1}")

        # 更新场景视图
        self._update_scenario_view()

        # 设置每日交互轮数
        self.interact_rounds_per_day = config.get("interact_rounds", 5)
        self.scenario_view.set_interact_rounds(self.interact_rounds_per_day)

        # 重置每日状态
        self.current_day = 1
        self.current_interact_round = 0
        self.total_dialogue_count = 0
        self.scenario_view.set_day(1)
        self.scenario_view.set_round(1)
        self.scenario_view.set_total_dialogue_count(0)

        # 开始模拟
        self.is_paused = False

        pygame.display.set_caption(f"多智能体社会模拟 - {scenario_name_map.get(scenario_type, '智能体模拟')}")

    def _create_random_agent(self, agent_id: str):
        """创建随机智能体"""
        import uuid

        # 随机数据
        names = ["小明", "小红", "小华", "小李", "小张", "小王", "小刘", "小陈",
                 "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
        mbtis = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                 "ISTJ", "ISTP", "ESTJ", "ESTP", "ISFJ", "ISFP", "ESFJ", "ESFP"]
        genders = ["男", "女"]
        occupations = ["学生", "教师", "工程师", "医生", "设计师", "艺术家"]
        backgrounds = [
            "热爱生活，喜欢探索新事物",
            "工作认真负责，追求完美",
            "善于社交，人缘很好",
            "内向安静，喜欢独立思考",
            "充满活力，喜欢冒险"
        ]

        name = random.choice(names)
        mbti = random.choice(mbtis)
        gender = random.choice(genders)
        occupation = random.choice(occupations)
        age = random.randint(18, 50)
        background = random.choice(backgrounds)

        # 创建智能体
        agent = BaseAgent(
            id=agent_id,
            name=name,
            mbti=mbti,
            gender=gender,
            age=age,
            background={
                "occupation": occupation,
                "education": "本科",
                "hometown": "北京",
                "description": background
            },
            appearance=f"{name}是一位{age}岁的{occupation}，{background}"
        )

        # 添加到世界
        if self.world:
            location = self.world.add_agent(agent_id, agent)
        else:
            location = None

        self.agents[agent_id] = agent
        self.name_to_id[agent.name] = agent_id
        return agent, location

    def _create_agent_from_data(self, agent_data: dict):
        """从数据创建智能体"""
        import uuid

        agent_id = str(uuid.uuid4())[:8]

        # 构建背景
        background = agent_data.get("background", "")
        if isinstance(background, str):
            bg_text = background
        else:
            bg_text = agent_data.get("occupation", "")

        agent = BaseAgent(
            id=agent_id,
            name=agent_data["name"],
            mbti=agent_data.get("mbti", "ENFP"),
            gender=agent_data.get("gender", "男"),
            age=int(agent_data.get("age", 25)),
            background={
                "occupation": agent_data.get("occupation", "未知"),
                "education": "本科",
                "hometown": "未知",
                "description": bg_text
            },
            appearance=f"{agent_data['name']}是一位{agent_data.get('age', 25)}岁"
        )

        # 添加到世界
        if self.world:
            location = self.world.add_agent(agent_id, agent)
        else:
            location = None

        self.agents[agent_id] = agent
        self.name_to_id[agent.name] = agent_id
        return agent, location

    def _update_scenario_view(self):
        """更新场景视图"""
        if not self.world:
            return

        # 添加智能体到视图
        for agent_id, agent in self.agents.items():
            location = self.world.get_agent_location(agent_id) if self.world else None
            if location:
                # 获取记忆数量和内容
                long_term_memories = getattr(agent, 'long_term_memory', []) or []
                short_term_memories = getattr(agent, 'short_term_memory', []) or []
                long_term_count = len(long_term_memories)
                short_term_count = len(short_term_memories)
                recent_memories = short_term_memories[-3:] if short_term_memories else []

                self.scenario_view.add_agent(
                    agent_id=agent_id,
                    name=agent.name,
                    mbti=agent.mbti,
                    location=location,
                    mood_value=agent.mood.get("value", 0.0),
                    wealth=agent.wealth,
                    long_term_memory_count=long_term_count,
                    short_term_memory_count=short_term_count,
                    short_term_memories=short_term_memories[-10:],  # 最近10条短期记忆
                    long_term_memories=long_term_memories[-10:],    # 最近10条长期记忆
                    recent_memories=recent_memories
                )

    def _simulate_step(self):
        """执行一步模拟"""
        if not self.world or not self.agents:
            return

        # 如果有scenario，使用scenario的完整逻辑
        if self.scenario:
            # 调用scenario的step方法
            self.current_step += 1
            step_result = self.scenario.step(self.agents, self.world, self.current_step)

            # 处理对话结果
            dialogues = step_result.get("dialogues", [])
            for dialogue in dialogues:
                location = dialogue.get("location", "")
                lines = dialogue.get("lines", [])

                # 找到说话agent并显示对话
                for line in lines:
                    speaker_name = line.get("speaker", "")
                    content = line.get("content", "")

                    # 使用name_to_id快速查找
                    agent_id = self.name_to_id.get(speaker_name)
                    if agent_id and agent_id in self.agents:
                        self.scenario_view.show_dialog(agent_id, content, duration=3.0)

            # 更新记忆统计
            self._sync_agent_memory_counts()

            # 更新轮数
            self.current_interact_round += 1
            self.scenario_view.set_round(self.current_interact_round)
            self.scenario_view.set_total_dialogue_count(self.total_dialogue_count)

        else:
            # 没有scenario时的简单处理（备用）
            for agent_id, agent in list(self.agents.items()):
                if random.random() < 0.3:  # 30%概率移动
                    current_loc = self.world.get_agent_location(agent_id)
                    if current_loc:
                        connected = self.world.get_connected_locations(current_loc)
                        if connected:
                            new_loc = random.choice(connected)
                            self.world.move_agent(agent, current_loc, new_loc)
                            self.scenario_view.move_agent(agent_id, current_loc, new_loc, duration=1.0)

    def _sync_agent_memory_counts(self):
        """同步智能体记忆数量到UI"""
        for agent_id, agent in self.agents.items():
            long_term_count = len(getattr(agent, 'long_term_memory', []) or [])
            short_term_count = len(getattr(agent, 'short_term_memory', []) or [])
            recent_memories = getattr(agent, 'short_term_memory', [])[-3:] if hasattr(agent, 'short_term_memory') else []
            long_term_memories = getattr(agent, 'long_term_memory', []) or []
            short_term_memories = getattr(agent, 'short_term_memory', []) or []

            self.scenario_view.update_agent_info(
                agent_id,
                long_term_memory_count=long_term_count,
                short_term_memory_count=short_term_count,
                short_term_memories=short_term_memories[-10:],
                long_term_memories=long_term_memories[-10:],
                recent_memories=recent_memories
            )

    def _end_current_day(self):
        """结束当前天，进入下一天"""
        if not self.world or not self.agents:
            return

        print(f"结束第 {self.current_day} 天")

        # 进入下一天
        self.current_day += 1
        self.current_interact_round = 0

        # 从输入框获取最新的每日轮数设置
        self.interact_rounds_per_day = self.scenario_view.get_interact_rounds()

        # 显示提示
        self._add_notification(f"第 {self.current_day} 天开始", duration=3.0)

        # 重置轮数显示
        self.scenario_view.set_round(1)
        self.scenario_view.set_day(self.current_day)

    def _handle_action(self, action: Optional[str]):
        """处理动作"""
        if action is None:
            return

        if action == "return_to_menu":
            self.current_view = "main"
            pygame.display.set_caption("多智能体社会模拟")
            return

        if action == "toggle_pause":
            self.is_paused = not self.is_paused

        elif action.startswith("speed:"):
            speed_str = action.split(":")[1]
            self.speed = float(speed_str)

        elif action == "step":
            self._simulate_step()

        elif action == "end_day":
            self._end_current_day()

        elif action.startswith("select:"):
            agent_id = action.split(":")[1]
            self.selected_agent_id = agent_id

    def run(self):
        """运行主循环"""
        running = True

        while running:
            if self.current_view == "main":
                # 主视图循环
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.session_panel.visible:
                                self.session_panel.visible = False
                            else:
                                running = False
                        # Ctrl+S 保存快捷键
                        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.save_current_session()
                        # 传递键盘事件给主视图（用于TextBox输入）
                        self.main_view.handle_event(event)
                    else:
                        self.main_view.handle_event(event)

                    # 处理Session面板事件
                    if self.session_panel.visible:
                        result = self.session_panel.handle_event(event)
                        if result == "close":
                            self.session_panel.visible = False
                        # select_session 只更新选中状态，不触发加载

                # 绘制主视图
                self.screen.fill((30, 33, 40))  # 背景色
                self.main_view.draw(self.screen)

                # 绘制Session面板（如果可见）
                if self.session_panel.visible:
                    # 半透明遮罩
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 128))
                    self.screen.blit(overlay, (0, 0))
                    self.session_panel.draw(self.screen)

                pygame.display.flip()

            elif self.current_view == "scenario":
                # 场景视图循环
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.session_panel.visible:
                                self.session_panel.visible = False
                            else:
                                self.current_view = "main"
                                pygame.display.set_caption("多智能体社会模拟")
                        elif event.key == pygame.K_SPACE:
                            self.is_paused = not self.is_paused
                        elif event.key == pygame.K_1:
                            self.speed = 1.0
                        elif event.key == pygame.K_2:
                            self.speed = 2.0
                        elif event.key == pygame.K_3:
                            self.speed = 4.0
                        elif event.key == pygame.K_s:
                            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                                # Ctrl+S 保存
                                self.save_current_session()
                            else:
                                self._simulate_step()
                    else:
                        action = self.scenario_view.handle_event(event)
                        self._handle_action(action)

                    # 处理Session面板事件
                    if self.session_panel.visible:
                        result = self.session_panel.handle_event(event)
                        if result == "close":
                            self.session_panel.visible = False
                        elif result and result.startswith("select_session:"):
                            session_id = result.split(":")[1]
                            self._on_load_session(session_id)

                # 自动步进
                if not self.is_paused:
                    current_time = time.time()
                    adjusted_interval = self.step_interval / self.speed
                    if current_time - self.last_step_time >= adjusted_interval:
                        self._simulate_step()
                        self.last_step_time = current_time

                # 更新和绘制
                self.scenario_view.update()
                self.scenario_view.draw(
                    selected_agent_id=self.selected_agent_id,
                    is_paused=self.is_paused,
                    speed=self.speed
                )

                # 绘制Session面板（如果可见）
                if self.session_panel.visible:
                    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 128))
                    self.screen.blit(overlay, (0, 0))
                    self.session_panel.draw(self.screen)

            self.clock.tick(60)

        pygame.quit()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多智能体社会模拟 - UI")
    parser.add_argument("--width", type=int, default=1280, help="窗口宽度")
    parser.add_argument("--height", type=int, default=800, help="窗口高度")
    parser.add_argument("--fast", action="store_true", help="快速模式（不调用LLM）")

    args = parser.parse_args()

    # 创建并运行UI
    ui = SimulationController(
        width=args.width,
        height=args.height,
        fast_mode=args.fast
    )
    ui.run()


if __name__ == "__main__":
    main()
