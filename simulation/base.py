"""
Simulation Base Classes - 抽象基类定义

定义智能体模拟系统的核心抽象接口：
- BaseEntity: 实体基类
- BaseAgent: 智能体基类
- BaseEnvironment: 环境基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class EntityState(Enum):
    """实体状态枚举"""
    IDLE = "idle"
    ACTIVE = "active"
    MOVING = "moving"
    INTERACTING = "interacting"
    RESTING = "resting"


@dataclass
class EntityEvent:
    """实体事件"""
    event_type: str
    entity_id: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)


class BaseEntity(ABC):
    """实体抽象基类

    所有可存在于环境中的实体（智能体、物品等）的基类。
    """

    def __init__(self, entity_id: str, name: str):
        self.id = entity_id
        self.name = name
        self.state = EntityState.IDLE
        self.position: Optional[str] = None
        self.events: List[EntityEvent] = []

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """更新实体状态"""
        pass

    def add_event(self, event: EntityEvent) -> None:
        """添加事件"""
        self.events.append(event)

    def get_events(self, event_type: Optional[str] = None) -> List[EntityEvent]:
        """获取事件列表"""
        if event_type is None:
            return self.events
        return [e for e in self.events if e.event_type == event_type]


class Memory:
    """记忆条目"""

    def __init__(self, content: str, timestamp: float, importance: float = 0.5):
        self.content = content
        self.timestamp = timestamp
        self.importance = importance

    def __repr__(self):
        return f"Memory(content={self.content[:30]}..., timestamp={self.timestamp})"


class BaseAgent(BaseEntity, ABC):
    """智能体抽象基类

    定义智能体的核心接口：
    - think(): 思考/生成回复
    - perceive(): 感知事件
    - act(): 采取行动
    - remember(): 记忆
    """

    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)

        self.short_term_memory: List[Memory] = []
        self.long_term_memory: List[Memory] = []

        self.mood: Dict[str, Any] = {"value": 0.0, "description": "平静"}
        self.personality: Dict[str, Any] = {}

        self.wealth: Dict[str, float] = {
            "time": 0.0,
            "social": 0.0,
            "health": 0.0,
            "mental": 0.0,
            "money": 0.0
        }

    @abstractmethod
    def think(self, prompt: str) -> str:
        """思考并生成回复

        Args:
            prompt: 输入提示词

        Returns:
            str: 生成的回复
        """
        pass

    @abstractmethod
    def perceive(self, event: EntityEvent) -> None:
        """感知事件

        Args:
            event: 事件对象
        """
        pass

    @abstractmethod
    def act(self) -> Dict[str, Any]:
        """采取行动

        Returns:
            Dict[str, Any]: 行动结果
        """
        pass

    def remember(self, content: str, importance: float = 0.5, is_long_term: bool = False) -> None:
        """记忆

        Args:
            content: 记忆内容
            importance: 重要性 (0-1)
            is_long_term: 是否为长期记忆
        """
        memory = Memory(content, time.time(), importance)

        if is_long_term:
            self.long_term_memory.append(memory)
            max_long_term = 200
            if len(self.long_term_memory) > max_long_term:
                self.long_term_memory = self.long_term_memory[-max_long_term:]
        else:
            self.short_term_memory.append(memory)
            max_short_term = 50
            if len(self.short_term_memory) > max_short_term:
                self.short_term_memory = self.short_term_memory[-max_short_term:]

    def get_recent_memories(self, count: int = 5) -> List[str]:
        """获取最近的记忆

        Args:
            count: 获取的记忆数量

        Returns:
            List[str]: 记忆内容列表
        """
        memories = self.short_term_memory[-count:] if self.short_term_memory else []
        return [m.content for m in memories]

    def update_mood(self, mood_type: str, delta: float, reason: str = "") -> None:
        """更新心情

        Args:
            mood_type: 心情类型
            delta: 变化量
            reason: 变化原因
        """
        new_value = self.mood["value"] + delta
        self.mood["value"] = max(-1.0, min(1.0, new_value))

        if self.mood["value"] > 0.7:
            self.mood["description"] = "非常开心"
        elif self.mood["value"] > 0.3:
            self.mood["description"] = "开心"
        elif self.mood["value"] > -0.3:
            self.mood["description"] = "平静"
        elif self.mood["value"] > -0.7:
            self.mood["description"] = "低落"
        else:
            self.mood["description"] = "非常低落"


class BaseEnvironment(ABC):
    """环境抽象基类

    定义环境的核心接口：
    - add_entity(): 添加实体
    - remove_entity(): 移除实体
    - get_neighbors(): 获取附近实体
    - tick(): 时间推进
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.entities: Dict[str, BaseEntity] = {}
        self.time: float = 0.0
        self.time_scale: float = 1.0  # 时间流速

    @abstractmethod
    def add_entity(self, entity: BaseEntity, position: Optional[str] = None) -> bool:
        """添加实体

        Args:
            entity: 实体对象
            position: 位置（可选）

        Returns:
            bool: 是否添加成功
        """
        pass

    @abstractmethod
    def remove_entity(self, entity_id: str) -> bool:
        """移除实体

        Args:
            entity_id: 实体ID

        Returns:
            bool: 是否移除成功
        """
        pass

    @abstractmethod
    def get_neighbors(self, entity_id: str, radius: float = 1.0) -> List[BaseEntity]:
        """获取附近的实体

        Args:
            entity_id: 实体ID
            radius: 搜索半径

        Returns:
            List[BaseEntity]: 附近实体列表
        """
        pass

    @abstractmethod
    def tick(self, delta_time: float = 1.0) -> None:
        """时间推进

        Args:
            delta_time: 时间增量
        """
        pass

    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """获取实体

        Args:
            entity_id: 实体ID

        Returns:
            Optional[BaseEntity]: 实体对象
        """
        return self.entities.get(entity_id)

    def get_all_entities(self) -> List[BaseEntity]:
        """获取所有实体

        Returns:
            List[BaseEntity]: 实体列表
        """
        return list(self.entities.values())
