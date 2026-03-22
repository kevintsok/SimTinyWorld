"""
Session - 会话管理模块

提供模拟会话的创建、保存、加载、删除和导出导入功能。
每个Session维护独立的模拟状态，支持保存/恢复/并发。
"""

from session.manager import SessionManager, SessionMetadata

__all__ = ["SessionManager", "SessionMetadata"]