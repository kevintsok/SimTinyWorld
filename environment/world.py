import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random
from environment.layout import EnvironmentLayout, EnvironmentVisualizer

@dataclass
class Location:
    name: str
    type: str
    description: str
    connected_locations: List[str]
    current_agents: List[str]  # 存储当前在该位置的智能体ID

class World:
    """表示智能体所在的世界环境"""
    
    def __init__(self, visual_mode=False, location_count=8):
        # 是否使用可视化模式
        self.visual_mode = visual_mode
        
        # 创建布局
        self.layout = EnvironmentLayout(location_count=location_count)
        
        # 从布局创建位置对象
        self.locations = {}
        for name, info in self.layout.locations.items():
            # 获取与该位置相连的位置列表
            connected_locations = self.layout.get_connected_locations(name)
            
            # 创建位置对象，使用默认类型和从布局中获取的描述
            self.locations[name] = Location(
                name=name,
                type="场所",  # 默认类型
                description=info["description"],
                connected_locations=connected_locations,
                current_agents=[]
            )
        
        # 智能体信息缓存
        self.agents = {}  # {agent_id: agent_obj}
        
        # 创建可视化器（在主线程中运行）
        self.visualizer = None
        self.is_visualizer_active = False
    
    def _init_visualizer(self):
        """初始化可视化器"""
        if not self.visual_mode:
            return
            
        if self.visualizer is None:
            self.visualizer = EnvironmentVisualizer(self.layout)
            self.is_visualizer_active = True
            
            # 不再创建新线程，而是在update_world方法中更新可视化
    
    def update_world(self):
        """更新世界状态，包括可视化"""
        if self.visual_mode and self.visualizer and self.is_visualizer_active:
            self.is_visualizer_active = self.visualizer.update_and_draw()
        return self.is_visualizer_active
    
    def add_agent(self, agent, location: str):
        """将智能体添加到指定位置"""
        # 检查位置是否存在
        if location not in self.locations:
            print(f"位置 {location} 不存在")
            return False
        
        # 将智能体添加到位置
        self.locations[location].current_agents.append(agent.id)
        
        # 缓存智能体信息
        self.agents[agent.id] = agent
        
        # 初始化可视化器（仅在可视化模式下）
        self._init_visualizer()
        
        # 添加智能体到可视化器（仅在可视化模式下）
        if self.visual_mode and self.visualizer:
            self.visualizer.add_agent(agent.id, agent.name, location)
        
        # 添加到智能体记忆
        agent.add_memory(
            f"我来到了{location}。{self.locations[location].description}",
            is_long_term=True
        )
        
        return True
    
    def move_agent(self, agent_id: str, target_location: str) -> bool:
        """将智能体从当前位置移动到目标位置"""
        # 检查智能体是否存在
        if agent_id not in self.agents:
            print(f"智能体 {agent_id} 不存在")
            return False
        
        # 检查目标位置是否存在
        if target_location not in self.locations:
            print(f"位置 {target_location} 不存在")
            return False
        
        # 获取智能体当前位置
        current_location = None
        for name, location in self.locations.items():
            if agent_id in location.current_agents:
                current_location = name
                break
        
        # 如果未找到当前位置，说明智能体不在任何位置
        if current_location is None:
            print(f"智能体 {agent_id} 不在任何位置")
            return False
        
        # 检查当前位置和目标位置是否有连接
        if target_location not in self.layout.get_connected_locations(current_location):
            print(f"{current_location} 和 {target_location} 之间没有直接连接")
            return False
        
        # 从当前位置移除智能体
        self.locations[current_location].current_agents.remove(agent_id)
        
        # 将智能体添加到目标位置
        self.locations[target_location].current_agents.append(agent_id)
        
        # 更新可视化器中的智能体位置（仅在可视化模式下）
        if self.visual_mode and self.visualizer:
            # 获取两地之间的距离作为动画时长
            distance = self.layout.get_distance(current_location, target_location)
            # 确保distance是数字类型，并且处理None情况
            try:
                duration = float(distance) * 0.5 if distance is not None else 1.0  # 距离越大，动画时间越长
            except (TypeError, ValueError):
                # 如果distance不能转换为float，使用默认值
                duration = 1.0
            self.visualizer.move_agent(agent_id, target_location, duration)
        
        # 添加移动记忆
        agent = self.agents[agent_id]
        agent.add_memory(
            f"我从{current_location}移动到了{target_location}。{self.locations[target_location].description}",
            is_long_term=True
        )
        
        return True
    
    def get_agents_at_location(self, location: str) -> List[Any]:
        """获取在指定位置的所有智能体"""
        if location not in self.locations:
            return []
        
        return [self.agents[agent_id] for agent_id in self.locations[location].current_agents
                if agent_id in self.agents]
    
    def get_connected_locations(self, location: str) -> List[str]:
        """获取与指定位置直接相连的所有位置"""
        return self.layout.get_connected_locations(location)
    
    def add_agent_dialog(self, agent_name: str, text: str):
        """在可视化器中添加智能体对话"""
        if self.visual_mode and self.visualizer:
            self.visualizer.add_dialog(agent_name, text)
    
    def get_random_location(self) -> str:
        """随机返回一个位置名称"""
        return random.choice(list(self.locations.keys())) 