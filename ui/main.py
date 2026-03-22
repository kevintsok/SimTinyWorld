"""
UI Main Entry Point - UI主入口

启动游戏风格可视化界面。
使用新的模块化UI：MainView（主界面）和 ScenarioView（场景视图）。
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
from environment.world import World
from environment.layout import EnvironmentLayout
from agent.base_agent import BaseAgent


class SimulationController:
    """模拟UI主控制器

    集成MainView（主界面）和ScenarioView（场景视图），
    管理两者之间的切换和数据流动。
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

        # 创建主视图（带回调接口）
        main_interface = MainViewInterface(
            on_scenario_selected=self._on_scenario_selected,
            on_agent_created=self._on_agent_created,
            on_agent_imported=self._on_agent_imported,
            on_quick_start=self._on_quick_start
        )
        self.main_view = MainView(self.screen, pygame.Rect(0, 0, width, height), main_interface)

        # 创建场景视图（带回调接口，使用共享的screen）
        scenario_interface = ScenarioViewInterface(
            on_agent_selected=self._on_agent_selected,
            on_agent_detail_toggle=self._on_agent_detail_toggle,
            on_return_to_menu=self._on_return_to_menu,
            on_simulation_control=self._on_simulation_control
        )
        self.scenario_view = ScenarioView(width, height, scenario_interface, self.screen)

        # 状态
        self.current_view = "main"  # main, scenario
        self.is_paused = True
        self.speed = 1.0
        self.selected_agent_id: Optional[str] = None

        # 模拟数据
        self.agents: Dict[str, BaseAgent] = {}
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

    def _start_simulation(self, config: dict):
        """开始模拟"""
        self.current_view = "scenario"

        # 初始化世界
        location_count = config.get("locations", 5)
        self.world = World(visual_mode=False, location_count=location_count)

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

        # 随机移动一些智能体
        for agent_id, agent in list(self.agents.items()):
            if random.random() < 0.3:  # 30%概率移动
                current_loc = self.world.get_agent_location(agent_id)
                if current_loc:
                    connected = self.world.get_connected_locations(current_loc)
                    if connected:
                        new_loc = random.choice(connected)
                        self.world.move_agent(agent, current_loc, new_loc)
                        self.scenario_view.move_agent(agent_id, current_loc, new_loc, duration=1.0)

        # 随机显示对话
        dialogue_this_round = 0
        for agent_id, agent in list(self.agents.items()):
            if random.random() < 0.2:  # 20%概率说话
                if self.fast_mode:
                    texts = [
                        "今天天气真好！", "你好！", "最近怎么样？",
                        "有什么新鲜事吗？", "一起出去走走吧！",
                        "这个项目很有趣", "我同意你的看法"
                    ]
                else:
                    texts = [
                        f"我是{agent.name}",
                        f"我的MBTI是{agent.mbti}",
                        agent.mood.get("description", "平静")
                    ]
                text = random.choice(texts)
                self.scenario_view.show_dialog(agent_id, text, duration=2.0)
                # 添加到智能体短期记忆
                agent.add_memory(f"在模拟中发言: {text}")
                dialogue_this_round += 1

        # 累计对话次数
        self.total_dialogue_count += dialogue_this_round

        # 更新记忆统计
        self._sync_agent_memory_counts()

        # 更新当前交互轮数
        self.current_interact_round += 1
        self.scenario_view.set_round(self.current_interact_round)
        self.scenario_view.set_total_dialogue_count(self.total_dialogue_count)

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
        self.scenario_view.event_notifications.append({
            "content": f"第 {self.current_day} 天开始",
            "start_time": time.time(),
            "duration": 3.0
        })

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
                            running = False
                        # 传递键盘事件给主视图（用于TextBox输入）
                        self.main_view.handle_event(event)
                    else:
                        self.main_view.handle_event(event)

                # 绘制主视图
                self.screen.fill((30, 33, 40))  # 背景色
                self.main_view.draw(self.screen)
                pygame.display.flip()

            elif self.current_view == "scenario":
                # 场景视图循环
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
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
                            self._simulate_step()
                    else:
                        action = self.scenario_view.handle_event(event)
                        self._handle_action(action)

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
