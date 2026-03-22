"""
Session Manager - 会话管理器

负责管理模拟会话的创建、保存、加载、删除和导出导入。
每个Session维护独立的模拟状态，支持保存/恢复/并发。
"""

import os
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class SessionMetadata:
    """Session元数据"""
    session_id: str
    name: str
    description: str
    created_at: float  # Unix timestamp
    updated_at: float  # Unix timestamp
    scenario_type: str
    agent_count: int
    current_day: int = 0
    current_step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMetadata":
        return cls(**data)


class SessionManager:
    """会话管理器

    核心功能：
    - create_session: 创建新会话
    - save_session: 保存会话状态
    - load_session: 加载会话
    - delete_session: 删除会话
    - list_sessions: 列出所有会话
    - export_session: 导出会话到指定路径
    - import_session: 从指定路径导入会话
    """

    SESSIONS_DIR = "sessions"

    def __init__(self, base_dir: str = None):
        """初始化会话管理器

        Args:
            base_dir: 基础目录，默认为当前工作目录
        """
        self.base_dir = base_dir or os.getcwd()
        self.sessions_dir = os.path.join(self.base_dir, self.SESSIONS_DIR)
        self._ensure_sessions_dir()

    def _ensure_sessions_dir(self):
        """确保sessions目录存在"""
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _get_session_path(self, session_id: str) -> str:
        """获取会话目录路径"""
        return os.path.join(self.sessions_dir, session_id)

    def _get_metadata_path(self, session_id: str) -> str:
        """获取元数据文件路径"""
        return os.path.join(self._get_session_path(session_id), "metadata.json")

    def _get_state_path(self, session_id: str) -> str:
        """获取状态文件路径"""
        return os.path.join(self._get_session_path(session_id), "state.json")

    def _get_agents_dir(self, session_id: str) -> str:
        """获取智能体目录路径"""
        return os.path.join(self._get_session_path(session_id), "agents")

    def create_session(
        self,
        name: str,
        description: str = "",
        scenario_type: str = "daily_life"
    ) -> str:
        """创建新会话

        Args:
            name: 会话名称
            description: 会话描述
            scenario_type: 场景类型

        Returns:
            str: 新会话的ID
        """
        # 生成会话ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"

        # 创建会话目录
        session_path = self._get_session_path(session_id)
        os.makedirs(session_path, exist_ok=True)
        os.makedirs(self._get_agents_dir(session_id), exist_ok=True)

        # 创建元数据
        metadata = SessionMetadata(
            session_id=session_id,
            name=name,
            description=description,
            created_at=datetime.now().timestamp(),
            updated_at=datetime.now().timestamp(),
            scenario_type=scenario_type,
            agent_count=0,
            current_day=0,
            current_step=0
        )

        # 保存元数据
        with open(self._get_metadata_path(session_id), "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

        return session_id

    def save_session(
        self,
        session_id: str,
        engine_state: Dict[str, Any],
        world_state: Dict[str, Any],
        scenario_state: Dict[str, Any],
        controller_state: Dict[str, Any],
        agents_data: Dict[str, Dict[str, Any]]
    ) -> bool:
        """保存会话状态

        Args:
            session_id: 会话ID
            engine_state: 引擎状态 (from SimulationEngine.to_dict())
            world_state: 世界状态 (from World.to_dict())
            scenario_state: 场景状态 (from DailyLifeScenario.to_dict())
            controller_state: 控制器状态
            agents_data: 智能体数据字典 {agent_id: agent_dict}

        Returns:
            bool: 是否保存成功
        """
        session_path = self._get_session_path(session_id)
        if not os.path.exists(session_path):
            # Session不存在，创建目录
            os.makedirs(session_path, exist_ok=True)
            os.makedirs(self._get_agents_dir(session_id), exist_ok=True)
            # 创建默认元数据
            metadata = SessionMetadata(
                session_id=session_id,
                name=session_id,
                description="",
                created_at=datetime.now().timestamp(),
                updated_at=datetime.now().timestamp(),
                scenario_type="daily_life",
                agent_count=0,
                current_day=0,
                current_step=0
            )
            with open(self._get_metadata_path(session_id), "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

        try:
            # 更新元数据
            metadata = self.load_metadata(session_id)
            if metadata:
                metadata.updated_at = datetime.now().timestamp()
                metadata.agent_count = len(agents_data)
                metadata.current_step = engine_state.get("current_step", 0)
                metadata.current_day = scenario_state.get("current_day", 0)

                with open(self._get_metadata_path(session_id), "w", encoding="utf-8") as f:
                    json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

            # 保存完整状态
            state = {
                "engine": engine_state,
                "world": world_state,
                "scenario": scenario_state,
                "controller": controller_state
            }

            with open(self._get_state_path(session_id), "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            # 保存智能体数据
            agents_dir = self._get_agents_dir(session_id)
            for agent_id, agent_dict in agents_data.items():
                agent_path = os.path.join(agents_dir, f"{agent_id}.json")
                with open(agent_path, "w", encoding="utf-8") as f:
                    json.dump(agent_dict, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话

        Args:
            session_id: 会话ID

        Returns:
            Dict containing metadata, state, and agents, or None if not found
        """
        session_path = self._get_session_path(session_id)
        if not os.path.exists(session_path):
            print(f"Session {session_id} does not exist")
            return None

        try:
            result = {}

            # 加载元数据
            metadata = self.load_metadata(session_id)
            if not metadata:
                return None
            result["metadata"] = metadata

            # 加载状态
            state_path = self._get_state_path(session_id)
            if os.path.exists(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    result["state"] = json.load(f)
            else:
                result["state"] = None

            # 加载智能体数据
            agents_dir = self._get_agents_dir(session_id)
            result["agents"] = {}
            if os.path.exists(agents_dir):
                for filename in os.listdir(agents_dir):
                    if filename.endswith(".json"):
                        agent_id = filename[:-5]  # 去掉 .json
                        agent_path = os.path.join(agents_dir, filename)
                        with open(agent_path, "r", encoding="utf-8") as f:
                            result["agents"][agent_id] = json.load(f)

            return result

        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def load_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """加载会话元数据

        Args:
            session_id: 会话ID

        Returns:
            SessionMetadata or None
        """
        metadata_path = self._get_metadata_path(session_id)
        if not os.path.exists(metadata_path):
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SessionMetadata.from_dict(data)
        except Exception as e:
            print(f"Error loading metadata for {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否删除成功
        """
        session_path = self._get_session_path(session_id)
        if not os.path.exists(session_path):
            print(f"Session {session_id} does not exist")
            return False

        try:
            shutil.rmtree(session_path)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    def list_sessions(self) -> List[SessionMetadata]:
        """列出所有会话

        Returns:
            List of SessionMetadata sorted by updated_at descending
        """
        sessions = []

        if not os.path.exists(self.sessions_dir):
            return sessions

        for session_id in os.listdir(self.sessions_dir):
            metadata = self.load_metadata(session_id)
            if metadata:
                sessions.append(metadata)

        # 按更新时间降序排列
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions

    def export_session(self, session_id: str, target_path: str) -> bool:
        """导出会话到指定路径

        Args:
            session_id: 会话ID
            target_path: 目标路径（可以是目录或zip文件路径）

        Returns:
            bool: 是否导出成功
        """
        session_path = self._get_session_path(session_id)
        if not os.path.exists(session_path):
            print(f"Session {session_id} does not exist")
            return False

        try:
            # 如果目标路径是目录，则复制到该目录
            if os.path.isdir(target_path):
                target_dir = os.path.join(target_path, session_id)
            else:
                # 如果是文件路径，复制到父目录
                target_dir = os.path.join(os.path.dirname(target_path), session_id)

            shutil.copytree(session_path, target_dir, dirs_exist_ok=True)
            return True

        except Exception as e:
            print(f"Error exporting session {session_id}: {e}")
            return False

    def import_session(self, source_path: str, new_name: str = None) -> Optional[str]:
        """从指定路径导入会话

        Args:
            source_path: 源路径（会话目录或包含会话的目录）
            new_name: 新会话名称，如果为None则使用原名称

        Returns:
            str: 新会话ID，或None如果导入失败
        """
        if not os.path.exists(source_path):
            print(f"Source path {source_path} does not exist")
            return None

        try:
            source_session_dir = source_path

            # 读取源元数据以获取名称
            metadata_path = os.path.join(source_session_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                print(f"Invalid session at {source_path}: no metadata.json")
                return None

            with open(metadata_path, "r", encoding="utf-8") as f:
                old_metadata = json.load(f)

            # 创建新会话
            session_name = new_name or old_metadata.get("name", "Imported Session")
            description = old_metadata.get("description", "")
            scenario_type = old_metadata.get("scenario_type", "daily_life")

            new_session_id = self.create_session(session_name, description, scenario_type)

            # 复制会话数据
            target_path = self._get_session_path(new_session_id)
            source_agents_dir = os.path.join(source_session_dir, "agents")

            # 复制状态文件
            state_path = os.path.join(source_session_dir, "state.json")
            if os.path.exists(state_path):
                shutil.copy2(state_path, self._get_state_path(new_session_id))

            # 复制智能体文件
            if os.path.exists(source_agents_dir):
                target_agents_dir = self._get_agents_dir(new_session_id)
                for filename in os.listdir(source_agents_dir):
                    if filename.endswith(".json"):
                        shutil.copy2(
                            os.path.join(source_agents_dir, filename),
                            os.path.join(target_agents_dir, filename)
                        )

            # 更新元数据
            new_metadata = self.load_metadata(new_session_id)
            if new_metadata:
                new_metadata.agent_count = old_metadata.get("agent_count", 0)
                new_metadata.current_day = old_metadata.get("current_day", 0)
                new_metadata.current_step = old_metadata.get("current_step", 0)
                with open(self._get_metadata_path(new_session_id), "w", encoding="utf-8") as f:
                    json.dump(new_metadata.to_dict(), f, ensure_ascii=False, indent=2)

            return new_session_id

        except Exception as e:
            print(f"Error importing session: {e}")
            return None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话简要信息

        Args:
            session_id: 会话ID

        Returns:
            Dict with session info or None
        """
        metadata = self.load_metadata(session_id)
        if not metadata:
            return None

        return {
            "session_id": metadata.session_id,
            "name": metadata.name,
            "description": metadata.description,
            "scenario_type": metadata.scenario_type,
            "agent_count": metadata.agent_count,
            "current_day": metadata.current_day,
            "current_step": metadata.current_step,
            "created_at": datetime.fromtimestamp(metadata.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.fromtimestamp(metadata.updated_at).strftime("%Y-%m-%d %H:%M:%S")
        }