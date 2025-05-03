import time
import threading
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import random
from environment.layout import EnvironmentLayout, EnvironmentVisualizer

@dataclass
class Location:
    """世界中的一个位置"""
    name: str
    type: str
    description: str
    connected_locations: List[str]
    current_agents: Set[str]  # 存储agent_id
    
    def __init__(self, name: str, type: str, description: str, connected_locations: List[str]):
        self.name = name
        self.type = type
        self.description = description
        self.connected_locations = connected_locations
        self.current_agents = set()

class World:
    """表示智能体活动的世界"""
    
    # 单例实例
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取World类的单例实例
        
        Returns:
            Optional[World]: 当前World实例，如果未初始化则返回None
        """
        return cls._instance
    
    def __init__(self, visual_mode: bool = False, location_count: int = 5):
        """初始化世界
        
        Args:
            visual_mode: 是否启用可视化模式
            location_count: 要创建的位置数量
        """
        # 设置单例实例
        World._instance = self
        
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
                connected_locations=connected_locations
            )
        
        # 智能体信息缓存
        self.agents = {}  # {agent_id: agent_obj}
        
        # 可视化器相关
        self.visualizer = None
        self.is_visualizer_active = False
        
        # 如果启用可视化模式，初始化可视化器
        if visual_mode:
            self._init_visualizer()
            
    def init_locations(self, location_names):
        """初始化位置
        
        Args:
            location_names: 要创建的位置名称列表
        """
        # 重新初始化布局
        self.layout = EnvironmentLayout(location_count=len(location_names))
        
        # 清空现有位置
        self.locations = {}
        
        # 从布局创建位置对象
        for name, info in self.layout.locations.items():
            # 获取与该位置相连的位置列表
            connected_locations = self.layout.get_connected_locations(name)
            
            # 创建位置对象，使用默认类型和从布局中获取的描述
            self.locations[name] = Location(
                name=name,
                type="场所",  # 默认类型
                description=info["description"],
                connected_locations=connected_locations
            )
            
    def _create_locations(self, location_count: int):
        """创建位置
        
        已由__init__中的创建布局代码实现，此方法保留以支持修改后的代码
        """
        pass
    
    def _init_visualizer(self):
        """初始化可视化器
        
        在单独线程中启动可视化器，避免阻塞主线程
        """
        # 创建可视化器
        self.visualizer = EnvironmentVisualizer(self.layout)
        
        # 在单独线程中启动可视化器
        self.is_visualizer_active = True
        viz_thread = threading.Thread(target=self._run_visualizer)
        viz_thread.daemon = True  # 设为守护线程，这样主程序退出时，此线程也会退出
        viz_thread.start()
        
        # 等待可视化器初始化完成
        time.sleep(2)
    
    def _run_visualizer(self):
        """在单独线程中运行可视化器"""
        if self.visualizer:
            self.visualizer.run()
            
    def add_agent(self, agent_id: str, agent_obj, initial_location: str = None):
        """添加智能体到世界
        
        Args:
            agent_id: 智能体ID
            agent_obj: 智能体对象
            initial_location: 初始位置名称，如果为None，则随机选择一个位置
        """
        # 存储智能体对象
        self.agents[agent_id] = agent_obj
        
        # 如果未指定初始位置，随机选择一个
        if initial_location is None:
            initial_location = random.choice(list(self.locations.keys()))
        
        # 检查指定的位置是否存在
        if initial_location not in self.locations:
            raise ValueError(f"位置 '{initial_location}' 不存在")
        
        # 将智能体添加到指定位置
        self.locations[initial_location].current_agents.add(agent_id)
        
        # 如果开启了可视化，添加智能体到可视化器
        if self.visual_mode and self.visualizer:
            self.visualizer.add_agent(agent_id, initial_location)
        
        return initial_location
    
    def add_agent_to_location(self, agent, location):
        """将智能体添加到指定位置（兼容性方法）
        
        Args:
            agent: 智能体对象
            location: 位置名称
            
        Returns:
            str: 添加的位置名称
        """
        return self.add_agent(agent.id, agent, location)
    
    def move_agent(self, agent, from_location: str, target_location: str) -> bool:
        """将智能体移动到新位置
        
        Args:
            agent: 智能体对象或智能体ID
            from_location: 当前位置名称
            target_location: 目标位置名称
            
        Returns:
            bool: 移动是否成功
        """
        # 确定智能体ID
        agent_id = agent.id if hasattr(agent, 'id') else agent
        
        # 检查目标位置是否存在
        if target_location not in self.locations:
            print(f"警告：位置 '{target_location}' 不存在")
            return False
        
        # 检查当前位置是否存在
        if from_location not in self.locations:
            print(f"警告：位置 '{from_location}' 不存在")
            return False
        
        # 检查智能体是否在当前位置
        if agent_id not in self.locations[from_location].current_agents:
            print(f"警告：智能体 '{agent_id}' 不在位置 '{from_location}'")
            return False
        
        # 检查是否可以移动到目标位置
        if target_location not in self.locations[from_location].connected_locations:
            # 使用布局计算目标位置是否可以访问
            distance = self.layout.get_distance(from_location, target_location)
            if distance is None or distance > 1:  # 距离为1表示直接相连
                print(f"警告：智能体不能从 '{from_location}' 直接移动到 '{target_location}'")
                return False
        
        # 从当前位置移除智能体
        self.locations[from_location].current_agents.remove(agent_id)
        
        # 添加智能体到新位置
        self.locations[target_location].current_agents.add(agent_id)
        
        # 如果开启了可视化，更新可视化器中的智能体位置
        if self.visual_mode and self.visualizer:
            self.visualizer.move_agent(agent_id, target_location)
        
        return True
    
    def get_agents_at_location(self, location_name: str) -> List[str]:
        """获取指定位置的所有智能体ID
        
        Args:
            location_name: 位置名称
            
        Returns:
            List[str]: 智能体ID列表
        """
        if location_name not in self.locations:
            print(f"警告：位置 '{location_name}' 不存在")
            return []
        
        return list(self.locations[location_name].current_agents)
    
    def get_agent_location(self, agent_id: str) -> Optional[str]:
        """获取智能体当前位置
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Optional[str]: 位置名称，如果智能体不存在则返回None
        """
        for loc_name, location in self.locations.items():
            if agent_id in location.current_agents:
                return loc_name
        return None
    
    def get_location_description(self, location_name: str) -> Optional[str]:
        """获取位置描述
        
        Args:
            location_name: 位置名称
            
        Returns:
            Optional[str]: 位置描述，如果位置不存在则返回None
        """
        if location_name not in self.locations:
            print(f"警告：位置 '{location_name}' 不存在")
            return None
        
        return self.locations[location_name].description
    
    def get_connected_locations(self, location_name: str) -> List[str]:
        """获取与指定位置相连的所有位置
        
        Args:
            location_name: 位置名称
            
        Returns:
            List[str]: 相连位置名称列表
        """
        if location_name not in self.locations:
            print(f"警告：位置 '{location_name}' 不存在")
            return []
        
        return self.locations[location_name].connected_locations
    
    def add_dialog(self, agent_id: str, text: str):
        """添加对话气泡到可视化器
        
        Args:
            agent_id: 智能体ID
            text: 对话内容
        """
        if self.visual_mode and self.visualizer:
            self.visualizer.add_dialog(agent_id, text)
    
    def get_all_locations(self) -> List[str]:
        """获取所有位置名称
        
        Returns:
            List[str]: 所有位置名称的列表
        """
        return list(self.locations.keys()) 