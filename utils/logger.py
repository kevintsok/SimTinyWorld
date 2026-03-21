import os
import time
import datetime
import threading

class SimulationLogger:
    """模拟日志记录工具
    
    记录模拟过程中的所有事件，包括每天模拟的过程、智能体对话等，
    将日志保存到logs/时间戳目录下
    """
    
    def __init__(self, simulation_id=None):
        """初始化日志记录器
        
        Args:
            simulation_id: 模拟ID，默认为当前时间戳
        """
        # 如果未提供模拟ID，使用当前时间戳
        if simulation_id is None:
            self.simulation_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.simulation_id = simulation_id
            
        # 创建线程锁，确保线程安全 - 必须在使用前初始化
        self.log_lock = threading.Lock()
            
        # 创建日志目录
        self.log_dir = f"logs/{self.simulation_id}"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建不同类型的日志文件
        self.simulation_log = os.path.join(self.log_dir, "simulation.log")
        self.dialogue_log = os.path.join(self.log_dir, "dialogues.log")
        self.action_log = os.path.join(self.log_dir, "actions.log")
        self.error_log = os.path.join(self.log_dir, "errors.log")
        
        # 初始化日志文件
        self._write_header(self.simulation_log, "模拟主日志")
        self._write_header(self.dialogue_log, "智能体对话日志")
        self._write_header(self.action_log, "智能体行动日志")
        self._write_header(self.error_log, "错误日志")
        
        # 记录模拟开始
        self.log_simulation(f"模拟开始 - ID: {self.simulation_id}")
        
    def _write_header(self, log_file, title):
        """写入日志文件头部信息
        
        Args:
            log_file: 日志文件路径
            title: 日志标题
        """
        with self.log_lock:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"======================================\n")
                f.write(f"  {title}\n")
                f.write(f"  模拟ID: {self.simulation_id}\n")
                f.write(f"  开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"======================================\n\n")
            
    def _write_log(self, log_file, message):
        """写入日志信息
        
        Args:
            log_file: 日志文件路径
            message: 日志消息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.log_lock:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
            
    def log_simulation(self, message):
        """记录模拟过程的日志
        
        Args:
            message: 日志消息
        """
        self._write_log(self.simulation_log, message)
        
    def log_round(self, day, round_num, total_rounds):
        """记录模拟轮次信息
        
        Args:
            day: 天数
            round_num: 当前轮次
            total_rounds: 总轮次
        """
        self._write_log(self.simulation_log, f"第{day}天 第{round_num}轮活动开始（总第{round_num + (day-1)*total_rounds}轮）")
        
    def log_dialogue(self, location, agents, dialogue_content):
        """记录智能体对话
        
        Args:
            location: 对话发生的位置
            agents: 参与对话的智能体列表
            dialogue_content: 对话内容
        """
        agent_names = [agent.name for agent in agents]
        message = f"对话位置: {location}\n"
        message += f"参与者: {', '.join(agent_names)}\n"
        message += f"对话内容:\n{dialogue_content}\n"
        message += "-" * 40 + "\n"
        self._write_log(self.dialogue_log, message)
        
    def log_agent_action(self, agent, action, location):
        """记录智能体行动
        
        Args:
            agent: 执行行动的智能体
            action: 行动描述
            location: 行动发生的位置
        """
        message = f"{agent.name} ({agent.mbti}, {agent.mood['description']}) 在 {location}: {action}"
        self._write_log(self.action_log, message)
        
    def log_agent_move(self, agent, from_location, to_location):
        """记录智能体移动
        
        Args:
            agent: 移动的智能体
            from_location: 起始位置
            to_location: 目标位置
        """
        message = f"{agent.name} 从 {from_location} 移动到 {to_location}"
        self._write_log(self.action_log, message)
        
    def log_agent_memory(self, agent, memory):
        """记录智能体形成的记忆
        
        Args:
            agent: 智能体
            memory: 记忆内容
        """
        message = f"{agent.name} 记忆: {memory}"
        self._write_log(self.action_log, message)
        
    def log_error(self, error_message, agent=None):
        """记录错误信息
        
        Args:
            error_message: 错误消息
            agent: 相关的智能体（可选）
        """
        if agent:
            message = f"与 {agent.name} 相关的错误: {error_message}"
        else:
            message = f"错误: {error_message}"
        self._write_log(self.error_log, message)
        
    def log_sleep(self, agent, sleep_quality):
        """记录智能体睡眠
        
        Args:
            agent: 智能体
            sleep_quality: 睡眠质量信息
        """
        message = f"{agent.name} 睡眠质量: {sleep_quality['description']} ({sleep_quality['score']}/5) - {sleep_quality['reason']}"
        self._write_log(self.action_log, message)
        
    def log_day_summary(self, day, agents_info):
        """记录每天的总结
        
        Args:
            day: 天数
            agents_info: 智能体信息摘要
        """
        message = f"第{day}天结束 - 智能体状态摘要:\n"
        for info in agents_info:
            message += f"- {info}\n"
        self._write_log(self.simulation_log, message)
        
    def close(self):
        """关闭日志记录器，写入结束信息"""
        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.log_lock:
            for log_file in [self.simulation_log, self.dialogue_log, self.action_log, self.error_log]:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n======================================\n")
                    f.write(f"模拟结束时间: {end_time}\n")
                    f.write(f"======================================\n")
        
        # 记录模拟结束
        self.log_simulation(f"模拟结束 - ID: {self.simulation_id}") 