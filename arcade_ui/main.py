"""
UI Main Entry Point - Arcade版本

使用arcade库的多智能体社会模拟UI主入口。
集成MainView（主界面）和ScenarioView（场景视图），
管理两者之间的切换和数据流动。支持多Session管理。
"""

import arcade
import sys
import os
import argparse
import time
import random
import threading
from typing import Dict, List, Optional, Any, Tuple
from queue import Queue, Empty

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arcade_ui.main_view import MainView, MainViewInterface
from environment.world import World
from agent.base_agent import BaseAgent
from session import SessionManager
from simulation.scenarios.daily_life import DailyLifeScenario
from llm_engine.factory import get_global_engine, has_global_engine


from arcade_ui.scenario_view import ScenarioView, ScenarioViewInterface


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
        # 创建arcade窗口
        self.window = arcade.Window(width, height, "多智能体社会模拟")
        self.width = width
        self.height = height
        self.fast_mode = fast_mode

        # 连接绘制回调
        self.window.on_draw = self.on_draw
        self.window.on_mouse_press = self.on_mouse_press
        self.window.on_mouse_motion = self.on_mouse_motion

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
        self.main_view = MainView(
            self.window,
            rect_x=0, rect_y=0,
            rect_width=width, rect_height=height,
            interface=main_interface
        )

        # 创建场景视图（带回调接口）
        scenario_interface = ScenarioViewInterface(
            on_agent_selected=self._on_agent_selected,
            on_agent_detail_toggle=self._on_agent_detail_toggle,
            on_return_to_menu=self._on_return_to_menu,
            on_simulation_control=self._on_simulation_control,
            on_save_session=self._on_save_session_in_scenario,
            on_load_session=self._on_load_session_in_scenario
        )
        self.scenario_view = ScenarioView(width, height, scenario_interface)

        # Session面板
        self.session_panel_visible = False

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
        self.last_step_time = 0
        self.step_interval = 2.0  # 秒

        # 每日交互轮数状态
        self.current_day = 1
        self.interact_rounds_per_day = 5  # 默认每日5轮交互
        self.current_interact_round = 0
        self.total_dialogue_count = 0  # 累计对话次数

        # 当前场景类型
        self.scenario_type = "daily_life"

        # DailyLifeScenario实例
        self.scenario: Optional[DailyLifeScenario] = None

        # 异步模拟步进支持
        self.step_result_queue: Queue = Queue()
        self.is_step_running: bool = False
        self._step_lock: threading.Lock = threading.Lock()
        self._step_thread: Optional[threading.Thread] = None

        # 模拟步数计数器
        self.current_step = 0

        # 设置窗口的更新和绘制回调
        self.window.on_update = self.on_update
        self.window.on_draw = self.on_draw
        self.window.on_mouse_motion = self.on_mouse_motion
        self.window.on_mouse_press = self.on_mouse_press
        self.window.on_key_press = self.on_key_press
        self.window.on_key_release = self.on_key_release

        # 追踪鼠标位置
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_pressed = False

    # ==================== 回调方法 ====================

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
        print("Session面板点击")
        self.session_panel_visible = True

    def _on_agent_selected(self, agent_id: str):
        """智能体被选中"""
        self.selected_agent_id = agent_id
        print(f"智能体选中: {agent_id}")

    def _on_agent_detail_toggle(self, visible: bool):
        """详情显示状态变化"""
        print(f"详情显示: {visible}")

    def _on_return_to_menu(self):
        """返回主菜单"""
        self.current_view = "main"
        self.window.set_caption("多智能体社会模拟")
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
        self.save_current_session()

    def _on_load_session_in_scenario(self):
        """在仿真场景中加载Session"""
        print("加载Session")

    # ==================== 事件处理 ====================

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """处理鼠标移动事件"""
        self.mouse_x = x
        self.mouse_y = y
        if self.current_view == "main":
            self.main_view.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """处理鼠标点击事件"""
        self.mouse_pressed = True
        if self.current_view == "main":
            self.main_view.on_mouse_press(x, y, button, modifiers)
        elif self.current_view == "scenario":
            action = self.scenario_view.handle_event({
                "type": "mouse_press",
                "x": x, "y": y, "button": button
            })
            self._handle_action(action)
        self.mouse_pressed = False

    def on_key_press(self, symbol: int, modifiers: int):
        """处理键盘按下事件"""
        if self.current_view == "scenario":
            if symbol == arcade.key.ESCAPE:
                if self.session_panel_visible:
                    self.session_panel_visible = False
                else:
                    self.current_view = "main"
                    self.window.set_caption("多智能体社会模拟")
            elif symbol == arcade.key.SPACE:
                self.is_paused = not self.is_paused
            elif symbol == arcade.key.KEY_1:
                self.speed = 1.0
            elif symbol == arcade.key.KEY_2:
                self.speed = 2.0
            elif symbol == arcade.key.KEY_3:
                self.speed = 4.0
            elif symbol == arcade.key.S:
                if modifiers & arcade.key.MOD_CTRL:
                    self.save_current_session()
                else:
                    self._simulate_step()

    def on_key_release(self, symbol: int, modifiers: int):
        """处理键盘释放事件"""
        pass

    def _handle_action(self, action):
        """处理动作"""
        if action is None:
            return

        if action == "return_to_menu":
            self.current_view = "main"
            self.window.set_caption("多智能体社会模拟")
            return

        if action == "toggle_pause":
            self.is_paused = not self.is_paused
        elif action and action.startswith("speed:"):
            parts = action.split(":")
            if len(parts) >= 2 and parts[1]:
                try:
                    self.speed = float(parts[1])
                except ValueError:
                    self.speed = 1.0
        elif action == "step":
            self._simulate_step()
        elif action and action.startswith("select:"):
            parts = action.split(":")
            if len(parts) >= 2:
                self.selected_agent_id = parts[1]

    # ==================== 更新和绘制 ====================

    def on_update(self, delta_time: float):
        """更新逻辑"""
        if self.current_view == "scenario":
            self._process_step_results()

            if not self.is_paused:
                current_time = time.time()
                adjusted_interval = self.step_interval / self.speed
                if current_time - self.last_step_time >= adjusted_interval:
                    self._simulate_step()
                    self.last_step_time = current_time

            self.scenario_view.update()

    def on_draw(self):
        """绘制"""
        if self.current_view == "main":
            self.main_view.draw()
        elif self.current_view == "scenario":
            self.scenario_view.draw()

    # ==================== 模拟控制 ====================

    def _start_simulation(self, config: dict):
        """开始模拟"""
        self.current_view = "scenario"

        if not has_global_engine():
            get_global_engine("qwen", mock_mode=self.fast_mode)

        self.scenario_type = config.get("scenario_type", "daily_life")

        location_count = config.get("locations", 5)
        self.world = World(visual_mode=False, location_count=location_count)

        if self.scenario_type == "daily_life":
            scenario_config = {
                "fast_mode": self.fast_mode,
                "rounds_per_day": config.get("interact_rounds", 5)
            }
            self.scenario = DailyLifeScenario(config=scenario_config)
            self.scenario.world = self.world
            self.scenario.setup()
            self.scenario.rounds_per_day = config.get("interact_rounds", 5)
        else:
            self.scenario = None

        locations = {}
        for name, info in self.world.layout.locations.items():
            pos = self.world.layout.positions.get(name, (0, 0))
            locations[name] = {
                "type": info.get("type", "默认"),
                "description": info.get("description", ""),
                "position": pos
            }

        connections = {}
        for loc_name, loc in self.world.locations.items():
            connections[loc_name] = [
                (conn, self.world.layout.get_distance(loc_name, conn))
                for conn in loc.connected_locations
            ]

        self.scenario_view.set_locations(locations, connections)

        scenario_name_map = {
            "daily_life": "日常生活",
            "emergency": "突发事件",
            "debate": "观点辩论"
        }
        self.scenario_view.set_scenario_info(
            name=scenario_name_map.get(self.scenario_type, "智能体模拟"),
            scenario_type=self.scenario_type
        )

        agent_count = config.get("num_agents", 5)
        custom_agents = config.get("custom_agents", [])

        for agent_data in custom_agents:
            self._create_agent_from_data(agent_data)

        existing_count = len(self.agents)
        for i in range(agent_count - existing_count):
            self._create_random_agent(f"agent_{i+1}")

        self._update_scenario_view()

        self.interact_rounds_per_day = config.get("interact_rounds", 5)
        self.scenario_view.set_interact_rounds(self.interact_rounds_per_day)

        self.current_day = 1
        self.current_interact_round = 0
        self.total_dialogue_count = 0
        self.scenario_view.set_day(1)
        self.scenario_view.set_round(1)
        self.scenario_view.set_total_dialogue_count(0)

        self.is_paused = False
        self.window.set_caption(f"多智能体社会模拟 - {scenario_name_map.get(self.scenario_type, '智能体模拟')}")

    def _create_random_agent(self, agent_id: str):
        """创建随机智能体"""
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
            appearance=f"{name}是一位{age}岁的{occupation}，{background}",
            skip_llm_init=True
        )

        if self.world:
            self.world.add_agent(agent_id, agent)

        self.agents[agent_id] = agent
        self.name_to_id[agent.name] = agent_id
        return agent

    def _create_agent_from_data(self, agent_data: dict):
        """从数据创建智能体"""
        import uuid
        agent_id = str(uuid.uuid4())[:8]

        bg_text = agent_data.get("background", agent_data.get("occupation", ""))

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
            appearance=f"{agent_data['name']}是一位{agent_data.get('age', 25)}岁",
            skip_llm_init=True
        )

        if self.world:
            self.world.add_agent(agent_id, agent)

        self.agents[agent_id] = agent
        self.name_to_id[agent.name] = agent_id
        return agent

    def _update_scenario_view(self):
        """更新场景视图"""
        if not self.world:
            return

        for agent_id, agent in self.agents.items():
            location = self.world.get_agent_location(agent_id) if self.world else None
            if location:
                long_term_memories = getattr(agent, 'long_term_memory', []) or []
                short_term_memories = getattr(agent, 'short_term_memory', []) or []
                recent_memories = short_term_memories[-3:] if short_term_memories else []

                self.scenario_view.add_agent(
                    agent_id=agent_id,
                    name=agent.name,
                    mbti=agent.mbti,
                    location=location,
                    mood_value=agent.mood.get("value", 0.0) if hasattr(agent, 'mood') else 0.0,
                    wealth=agent.wealth if hasattr(agent, 'wealth') else {},
                    long_term_memory_count=len(long_term_memories),
                    short_term_memory_count=len(short_term_memories),
                    short_term_memories=short_term_memories[-10:],
                    long_term_memories=long_term_memories[-10:],
                    recent_memories=recent_memories
                )

    def _simulate_step(self):
        """执行一步模拟（异步版本，不阻塞UI）"""
        if not self.world or not self.agents:
            return

        with self._step_lock:
            if self.is_step_running:
                return
            self.is_step_running = True

        self._step_thread = threading.Thread(
            target=self._simulate_step_worker,
            args=(),
            daemon=True
        )
        self._step_thread.start()

    def _simulate_step_worker(self):
        """后台线程执行模拟步骤"""
        try:
            if self.scenario:
                step = self.current_step + 1
                step_result = self.scenario.step(self.agents, self.world, step)
                self.step_result_queue.put(("scenario", step_result, step))
            else:
                movements = []
                for agent_id, agent in list(self.agents.items()):
                    if random.random() < 0.3:
                        current_loc = self.world.get_agent_location(agent_id)
                        if current_loc:
                            connected = self.world.get_connected_locations(current_loc)
                            if connected:
                                new_loc = random.choice(connected)
                                self.world.move_agent(agent, current_loc, new_loc)
                                movements.append((agent_id, current_loc, new_loc))
                self.step_result_queue.put(("simple", movements, None))
        except Exception as e:
            print(f"模拟步骤执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            with self._step_lock:
                self.is_step_running = False

    def _process_step_results(self):
        """在主循环中处理模拟步骤结果（不阻塞）"""
        try:
            while True:
                result = self.step_result_queue.get_nowait()
                result_type, data, step = result

                if result_type == "scenario":
                    self.current_step = step

                    dialogues = data.get("dialogues", [])
                    for dialogue in dialogues:
                        lines = dialogue.get("lines", [])
                        for line in lines:
                            speaker_name = line.get("speaker", "")
                            content = line.get("content", "")
                            agent_id = self.name_to_id.get(speaker_name)
                            if agent_id and agent_id in self.agents:
                                self.scenario_view.show_dialog(agent_id, content, duration=3.0)

                    # 同步移动（修复：之前忽略了scenario类型的movements）
                    movements = data.get("movements", [])
                    for move in movements:
                        if isinstance(move, dict):
                            agent_name = move.get("agent", "")
                            from_loc = move.get("from", "")
                            to_loc = move.get("to", "")
                            agent_id = self.name_to_id.get(agent_name)
                        elif isinstance(move, (list, tuple)) and len(move) >= 3:
                            agent_id, from_loc, to_loc = move[0], move[1], move[2]
                        else:
                            continue
                        if agent_id and from_loc and to_loc:
                            self.scenario_view.move_agent(agent_id, from_loc, to_loc, duration=1.0)

                    self._sync_agent_memory_counts()

                    self.current_interact_round += 1
                    self.scenario_view.set_round(self.current_interact_round)
                    self.scenario_view.set_total_dialogue_count(self.total_dialogue_count)

                elif result_type == "simple":
                    for move in data:
                        if isinstance(move, (list, tuple)) and len(move) >= 3:
                            agent_id, from_loc, to_loc = move[0], move[1], move[2]
                            self.scenario_view.move_agent(agent_id, from_loc, to_loc, duration=1.0)

        except Empty:
            pass

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

    # ==================== Session管理 ====================

    def save_current_session(self) -> bool:
        """保存当前Session"""
        if not self.current_session_id:
            self.current_session_id = self.session_manager.create_session(
                name=self.current_session_name,
                description="",
                scenario_type=self.scenario_type
            )

        return self._save_current_session(self.current_session_id)

    def _save_current_session(self, session_id: str) -> bool:
        """保存指定Session"""
        world_state = self.world.to_dict() if self.world else {}
        scenario_state = self.scenario_view.to_dict()
        controller_state = self._to_dict()

        agents_data = {}
        for agent_id, agent in self.agents.items():
            agents_data[agent_id] = agent.to_dict()

        success = self.session_manager.save_session(
            session_id=session_id,
            engine_state={},
            world_state=world_state,
            scenario_state=scenario_state,
            controller_state=controller_state,
            agents_data=agents_data
        )

        if success:
            print(f"Session {session_id} 已保存")
        else:
            print(f"Session {session_id} 保存失败")

        return success

    def _to_dict(self) -> Dict[str, Any]:
        """将UI状态序列化为字典"""
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多智能体社会模拟 - Arcade UI")
    parser.add_argument("--width", type=int, default=1000, help="窗口宽度")
    parser.add_argument("--height", type=int, default=700, help="窗口高度")
    parser.add_argument("--fast", action="store_true", help="快速模式（不调用LLM）")

    args = parser.parse_args()

    controller = SimulationController(
        width=args.width,
        height=args.height,
        fast_mode=args.fast
    )
    arcade.run()


if __name__ == "__main__":
    main()
