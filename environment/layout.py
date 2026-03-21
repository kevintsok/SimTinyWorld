import json
import os
from typing import Dict, List, Tuple, Optional
import pygame
import random
import math
import time

# 定义节点类型和颜色映射
LOCATION_COLORS = {
    "公司": (100, 149, 237),  # 矢车菊蓝
    "公园": (60, 179, 113),   # 中等海洋绿
    "学校": (255, 165, 0),    # 橙色
    "医院": (220, 20, 60),    # 猩红色
    "餐厅": (218, 165, 32),   # 金菊黄
    "商场": (186, 85, 211),   # 中等兰花紫
    "图书馆": (139, 69, 19),  # 马鞍棕色
    "健身房": (50, 205, 50),  # 石灰绿
}

class EnvironmentLayout:
    """环境布局类，管理节点和路径"""
    
    def __init__(self, location_count=8):
        self.locations = {}  # 节点信息
        self.distances = {}  # 节点间距离
        self.positions = {}  # 可视化中节点的位置
        self.initialized = False
        self.default_locations = [
            "公司", "公园", "学校", "医院", "餐厅", "商场", "图书馆", "健身房",
            "咖啡厅", "银行", "电影院", "超市", "博物馆", "体育场", "社区中心", "酒店",
            "宠物店", "药店", "服装店", "水果店", "电子产品店", "家具店", "美术馆", "游戏厅",
            "书店", "面包店", "花店", "旅行社", "公寓", "洗衣店", "快递站", "景区"
        ]
        self.location_count = min(location_count, len(self.default_locations) * 10)  # 限制最大数量
        self._init_default_layout()
        
    def _init_default_layout(self):
        """初始化默认环境布局"""
        # 清空现有数据
        self.locations.clear()
        self.distances.clear()
        self.positions.clear()
        
        # 如果数量超过基础地点数量，需要生成带前缀的多个相同类型地点
        base_location_count = len(self.default_locations)
        
        # 生成地点
        for i in range(self.location_count):
            location_type = self.default_locations[i % base_location_count]
            
            # 如果需要创建多个同类型的地点，添加字母前缀
            if i >= base_location_count:
                prefix = chr(65 + (i // base_location_count) - 1)  # A, B, C...
                location_name = f"{prefix}{location_type}"
            else:
                location_name = location_type
            
            # 为不同地点添加不同的描述
            description = self._generate_description(location_name, location_type)
            self.add_location(location_name, description)
        
        # 构建连接网络 - 确保地图是连通的
        # 首先，将所有地点按照环形连接起来，确保基本连通性
        all_locations = list(self.locations.keys())
        for i in range(len(all_locations)):
            # 连接到下一个地点（最后一个连接到第一个）
            next_idx = (i + 1) % len(all_locations)
            self.add_connection(all_locations[i], all_locations[next_idx], random.randint(3, 8))
            
            # 添加一些额外的随机连接，增加地图复杂性
            # 每个地点平均有2-4个连接
            # 随机连接的总数大约是地点数量的1-2倍
            extra_connections = min(self.location_count // 2, 20)  # 限制最大额外连接数
            
        # 添加一些随机连接，使地图更加丰富
        for _ in range(extra_connections):
            loc1 = random.choice(all_locations)
            loc2 = random.choice(all_locations)
            # 避免自连接和重复连接
            if loc1 != loc2 and (loc1 not in self.distances or loc2 not in self.distances[loc1]):
                self.add_connection(loc1, loc2, random.randint(3, 10))
        
        # 设置完成标志
        self.initialized = True
    
    def _generate_description(self, location_name, location_type):
        """为地点生成描述"""
        # 基础描述
        base_descriptions = {
            "公司": "一个现代化的办公大楼，充满忙碌的员工",
            "公园": "一个宁静的绿色空间，有湖泊和步行道",
            "学校": "一所现代化的学校，有操场和教学楼",
            "医院": "一家设备先进的医院，医护人员来回穿梭",
            "餐厅": "一家温馨的餐厅，提供各种美食",
            "商场": "一个大型购物中心，里面有各种商店",
            "图书馆": "一座安静的图书馆，藏书丰富",
            "健身房": "一个设备齐全的健身场所",
            "咖啡厅": "一家舒适的咖啡厅，提供各种咖啡和点心",
            "银行": "一家现代化的银行，提供各种金融服务",
            "电影院": "一家现代化的电影院，有多个放映厅",
            "超市": "一家大型超市，商品种类齐全",
            "博物馆": "一座历史悠久的博物馆，展品丰富",
            "体育场": "一个大型体育场，可以举办各种体育赛事",
            "社区中心": "一个社区活动中心，提供各种社区服务",
            "酒店": "一家豪华酒店，提供舒适的住宿和餐饮",
            "宠物店": "一家专业的宠物店，提供各种宠物用品和服务",
            "药店": "一家专业的药店，提供各种药品和健康咨询",
            "服装店": "一家时尚的服装店，提供各种服装和配饰",
            "水果店": "一家新鲜的水果店，水果种类齐全",
            "电子产品店": "一家现代化的电子产品店，提供各种电子设备",
            "家具店": "一家专业的家具店，提供各种家具和家居用品",
            "美术馆": "一座精致的美术馆，展示各种艺术作品",
            "游戏厅": "一家热闹的游戏厅，提供各种电子游戏",
            "书店": "一家安静的书店，提供各种图书和文具",
            "面包店": "一家香气四溢的面包店，提供各种新鲜面包",
            "花店": "一家色彩缤纷的花店，提供各种鲜花和绿植",
            "旅行社": "一家专业的旅行社，提供各种旅游服务",
            "公寓": "一栋现代化的公寓楼，住宅环境舒适",
            "洗衣店": "一家干净整洁的洗衣店，提供各种洗衣服务",
            "快递站": "一个忙碌的快递站，负责收发各种包裹",
            "景区": "一个美丽的景区，自然风光优美"
        }
        
        # 如果是带前缀的地点，稍微修改描述以区分
        if location_name != location_type:
            prefix = location_name[0]  # 获取前缀
            base_desc = base_descriptions.get(location_type, f"一个{location_type}")
            
            # 根据前缀添加不同特点
            if prefix == 'A':
                return f"{base_desc}，规模较大，位于城市中心"
            elif prefix == 'B':
                return f"{base_desc}，环境优雅，位于城市东部"
            elif prefix == 'C':
                return f"{base_desc}，设施先进，位于城市西部"
            elif prefix == 'D':
                return f"{base_desc}，历史悠久，位于城市南部"
            elif prefix == 'E':
                return f"{base_desc}，风格现代，位于城市北部"
            else:
                return f"{base_desc}，{prefix}区分部"
        
        return base_descriptions.get(location_type, f"一个{location_type}")
    
    def add_location(self, name: str, description: str = ""):
        """添加位置节点"""
        self.locations[name] = {
            "name": name,
            "description": description
        }
        
        # 如果是第一次添加节点，生成一个随机的2D位置
        if name not in self.positions:
            # 使用固定种子以便位置确定性
            random.seed(hash(name))
            self.positions[name] = (
                random.randint(100, 700),  # x坐标
                random.randint(100, 500)   # y坐标
            )
    
    def add_connection(self, location1: str, location2: str, distance: int):
        """添加两个位置之间的连接和距离"""
        # 确保位置存在
        if location1 not in self.locations:
            raise ValueError(f"位置 {location1} 不存在")
        if location2 not in self.locations:
            raise ValueError(f"位置 {location2} 不存在")
        
        # 添加距离信息（无向图）
        if location1 not in self.distances:
            self.distances[location1] = {}
        if location2 not in self.distances:
            self.distances[location2] = {}
            
        self.distances[location1][location2] = distance
        self.distances[location2][location1] = distance
    
    def get_connected_locations(self, location: str) -> List[str]:
        """获取与指定位置直接相连的所有位置"""
        if location not in self.distances:
            return []
        return list(self.distances[location].keys())
    
    def get_distance(self, location1: str, location2: str) -> Optional[int]:
        """获取两个位置之间的距离"""
        if location1 in self.distances and location2 in self.distances[location1]:
            return self.distances[location1][location2]
        return None
    
    def save_to_file(self, filepath: str = "environment/layout_data.json"):
        """保存环境布局到文件"""
        data = {
            "locations": self.locations,
            "distances": self.distances,
            "positions": self.positions
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str = "environment/layout_data.json"):
        """从文件加载环境布局"""
        if not os.path.exists(filepath):
            print(f"布局文件 {filepath} 不存在，使用默认布局")
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.locations = data.get("locations", {})
        self.distances = data.get("distances", {})
        self.positions = data.get("positions", {})
        self.initialized = True


class EnvironmentVisualizer:
    """环境可视化器，用像素风格可视化环境"""
    
    def __init__(self, layout: EnvironmentLayout, width: int = 800, height: int = 600):
        self.layout = layout
        self.width = width
        self.height = height
        self.agents = {}  # 智能体信息 {id: {name, position, target, start_time, ...}}
        self.font = None
        self.node_images = {}  # 节点图像缓存
        self.dialog_boxes = []  # 对话框列表 [(agent_name, text, position, end_time), ...]
        self.running = False
        self.screen = None
        self.clock = None
        
        # 初始化Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("智能体模拟世界")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simsunnsimsun", 16)
        
        # 加载或创建像素风格的节点图像
        self._init_node_images()
    
    def _init_node_images(self, size: int = 64):
        """初始化节点图像"""
        for location_name, color in LOCATION_COLORS.items():
            # 创建一个临时surface绘制像素风格的图像
            image = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # 绘制主体建筑
            pygame.draw.rect(image, color, (10, 10, size-20, size-20))
            
            # 绘制屋顶或特征
            if location_name == "公司":
                # 办公楼风格
                pygame.draw.rect(image, (70, 130, 210), (10, 20, size-20, 10))
                pygame.draw.rect(image, (70, 130, 210), (10, 35, size-20, 10))
                pygame.draw.rect(image, (70, 130, 210), (10, 50, size-20, 10))
            elif location_name == "学校":
                # 学校风格
                pygame.draw.polygon(image, (255, 140, 0), [(10, 10), (size-10, 10), (size//2, 0)])
                pygame.draw.rect(image, (240, 130, 0), (25, 30, 15, 15))
                pygame.draw.rect(image, (240, 130, 0), (size-40, 30, 15, 15))
            elif location_name == "医院":
                # 医院标志
                pygame.draw.rect(image, (255, 255, 255), (size//2-5, 20, 10, 25))
                pygame.draw.rect(image, (255, 255, 255), (size//2-15, 30, 30, 5))
            elif location_name == "公园":
                # 树和湖泊
                pygame.draw.circle(image, (50, 150, 100), (20, 20), 8)
                pygame.draw.circle(image, (50, 150, 100), (40, 15), 10)
                pygame.draw.ellipse(image, (70, 130, 210), (15, 35, 30, 15))
            elif location_name == "餐厅":
                # 餐厅标志
                pygame.draw.ellipse(image, (255, 200, 100), (20, 20, 25, 15))
                pygame.draw.rect(image, (255, 200, 100), (30, 35, 5, 15))
            elif location_name == "商场":
                # 商场标志
                pygame.draw.rect(image, (200, 100, 200), (15, 25, 35, 20))
                pygame.draw.rect(image, (220, 120, 220), (25, 15, 15, 10))
            elif location_name == "图书馆":
                # 书籍图案
                for i in range(3):
                    pygame.draw.rect(image, (150+i*30, 70+i*20, 20), (15+i*10, 20, 5, 25))
            elif location_name == "健身房":
                # 哑铃图案
                pygame.draw.circle(image, (30, 180, 30), (20, 32), 8)
                pygame.draw.circle(image, (30, 180, 30), (44, 32), 8)
                pygame.draw.rect(image, (30, 180, 30), (20, 28, 24, 8))
                
            # 保存到缓存
            self.node_images[location_name] = image
    
    def add_agent(self, agent_id: str, agent_name: str, location: str):
        """添加一个智能体到可视化器"""
        if location not in self.layout.positions:
            print(f"警告: 位置 {location} 未在布局中定义")
            return
            
        # 随机生成智能体颜色
        random.seed(hash(agent_id))
        color = (
            random.randint(50, 250),
            random.randint(50, 250),
            random.randint(50, 250)
        )
        
        self.agents[agent_id] = {
            "id": agent_id,
            "name": agent_name,
            "location": location,
            "position": self.layout.positions[location],
            "target": None,  # 移动目标
            "start_pos": None,  # 移动起点
            "start_time": None,  # 移动开始时间
            "move_duration": None,  # 移动持续时间
            "color": color  # 智能体颜色
        }
    
    def move_agent(self, agent_id: str, target_location: str, duration: float = 1.0):
        """移动智能体到新位置"""
        if agent_id not in self.agents:
            print(f"警告: 智能体 {agent_id} 未在可视化器中定义")
            return
            
        if target_location not in self.layout.positions:
            print(f"警告: 位置 {target_location} 未在布局中定义")
            return
        
        # 确保duration是浮点数
        try:
            duration_float = float(duration)
        except (TypeError, ValueError):
            duration_float = 1.0  # 默认1秒
        
        agent = self.agents[agent_id]
        agent["target"] = target_location
        agent["start_pos"] = agent["position"]
        agent["start_time"] = time.time()
        agent["move_duration"] = duration_float
    
    def add_dialog(self, agent_name: str, text: str, duration: float = 3.0):
        """添加一个对话框"""
        # 找到对应智能体
        agent_pos = None
        for agent in self.agents.values():
            if agent["name"] == agent_name:
                agent_pos = agent["position"]
                break
        
        if agent_pos:
            # 确保文本不为None
            if text is None:
                text = ""
            
            # 确保duration是浮点数
            try:
                duration_float = float(duration)
            except (TypeError, ValueError):
                duration_float = 3.0  # 默认3秒
                
            self.dialog_boxes.append((
                agent_name, 
                text,
                agent_pos,
                time.time() + duration_float
            ))
    
    def update(self):
        """更新可视化状态"""
        # 更新智能体位置
        current_time = time.time()
        for agent_id, agent in self.agents.items():
            if agent["target"] and agent["start_time"]:
                # 计算移动进度，保证move_duration有效
                try:
                    if agent["move_duration"] <= 0:
                        progress = 1.0  # 如果持续时间无效，视为已完成
                    else:
                        progress = min(1.0, (current_time - agent["start_time"]) / agent["move_duration"])
                except (TypeError, ZeroDivisionError):
                    progress = 1.0  # 发生错误时视为已完成移动
                
                if progress < 1.0:
                    # 插值计算当前位置
                    start_x, start_y = agent["start_pos"]
                    target_x, target_y = self.layout.positions[agent["target"]]
                    
                    # 使用缓动函数使动画更自然
                    eased_progress = self._ease_out_quad(progress)
                    
                    current_x = start_x + (target_x - start_x) * eased_progress
                    current_y = start_y + (target_y - start_y) * eased_progress
                    
                    agent["position"] = (current_x, current_y)
                else:
                    # 移动完成
                    agent["position"] = self.layout.positions[agent["target"]]
                    agent["location"] = agent["target"]
                    agent["target"] = None
                    agent["start_pos"] = None
                    agent["start_time"] = None
        
        # 清理过期的对话框
        self.dialog_boxes = [box for box in self.dialog_boxes if box[3] > current_time]
    
    def _ease_out_quad(self, t: float) -> float:
        """缓动函数，使动画更自然"""
        try:
            t_float = float(t)
            return 1 - (1 - t_float) * (1 - t_float)
        except (TypeError, ValueError):
            return 0.0  # 如果输入无效，返回初始状态
    
    def draw(self):
        """绘制环境可视化"""
        # 填充背景
        self.screen.fill((240, 240, 240))
        
        # 绘制节点之间的连接
        for location1, connections in self.layout.distances.items():
            pos1 = self.layout.positions[location1]
            for location2, distance in connections.items():
                pos2 = self.layout.positions[location2]
                
                # 绘制连接线
                pygame.draw.line(self.screen, (180, 180, 180), pos1, pos2, 3)
                
                # 绘制距离文本
                mid_x = (pos1[0] + pos2[0]) / 2
                mid_y = (pos1[1] + pos2[1]) / 2
                
                # 计算偏移以避免文字和线重叠
                angle = math.atan2(pos2[1] - pos1[1], pos2[0] - pos1[0])
                offset_x = math.sin(angle) * 10
                offset_y = -math.cos(angle) * 10
                
                distance_text = self.font.render(str(distance), True, (0, 0, 0))
                distance_rect = distance_text.get_rect(center=(mid_x + offset_x, mid_y + offset_y))
                self.screen.blit(distance_text, distance_rect)
        
        # 绘制节点
        for location_name, position in self.layout.positions.items():
            # 获取节点图像
            node_image = self.node_images.get(location_name)
            if node_image:
                image_rect = node_image.get_rect(center=position)
                self.screen.blit(node_image, image_rect)
            else:
                # 如果没有图像，绘制一个圆形
                color = LOCATION_COLORS.get(location_name, (100, 100, 100))
                pygame.draw.circle(self.screen, color, position, 20)
            
            # 绘制位置名称
            name_text = self.font.render(location_name, True, (0, 0, 0))
            name_rect = name_text.get_rect(center=(position[0], position[1] + 40))
            self.screen.blit(name_text, name_rect)
        
        # 绘制智能体
        for agent_id, agent in self.agents.items():
            position = agent["position"]
            color = agent["color"]
            
            # 绘制智能体（像素风格小人）
            pygame.draw.circle(self.screen, color, position, 12)
            
            # 绘制名称
            name_text = self.font.render(agent["name"], True, (0, 0, 0))
            name_rect = name_text.get_rect(center=(position[0], position[1] - 20))
            self.screen.blit(name_text, name_rect)
        
        # 绘制对话框
        for dialog in self.dialog_boxes:
            self._draw_dialog_box(dialog)
        
        # 更新显示
        pygame.display.flip()
    
    def _draw_dialog_box(self, dialog):
        """绘制对话框"""
        agent_name, text, position, end_time = dialog
        
        # 处理None文本情况
        if text is None:
            text = ""
        
        # 计算对话框位置
        box_x = position[0] - 100
        box_y = position[1] - 100
        
        # 文本分行处理
        words = text.split(' ')
        lines = []
        line = ""
        for word in words:
            test_line = line + word + " "
            line_width = self.font.size(test_line)[0]
            if line_width < 190:  # 对话框宽度为200，减去一些边距
                line = test_line
            else:
                lines.append(line)
                line = word + " "
        lines.append(line)  # 添加最后一行
        
        # 计算对话框尺寸
        line_height = self.font.get_linesize()
        text_height = line_height * len(lines)
        box_width = 200
        box_height = text_height + 40
        
        # 对话框位置
        box_x = position[0] - box_width // 2
        box_y = position[1] - box_height - 30
        
        # 绘制对话框背景
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (box_x, box_y, box_width, box_height), 0, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), 
                        (box_x, box_y, box_width, box_height), 2, 10)
        
        # 绘制小三角指向智能体
        pygame.draw.polygon(self.screen, (255, 255, 255), [
            (position[0], position[1] - 18),
            (position[0] - 10, box_y + box_height),
            (position[0] + 10, box_y + box_height)
        ])
        
        # 绘制说话者名称
        name_text = self.font.render(f"{agent_name}:", True, (0, 0, 0))
        self.screen.blit(name_text, (box_x + 10, box_y + 10))
        
        # 绘制对话内容
        for i, line in enumerate(lines):
            line_text = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(line_text, (box_x + 10, box_y + 30 + i * line_height))
    
    def update_and_draw(self):
        """更新状态并绘制一帧，用于在主线程中调用"""
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
        
        # 更新状态
        self.update()
        
        # 绘制画面
        self.draw()
        
        # 控制帧率
        self.clock.tick(60)
        
        return self.running

    def run(self):
        """运行可视化循环"""
        self.running = True
        
        while self.running:
            self.update_and_draw()
            
        # 退出Pygame
        pygame.quit()
    
    def close(self):
        """关闭可视化器"""
        self.running = False
        pygame.quit()


# 测试代码
if __name__ == "__main__":
    # 创建环境布局
    layout = EnvironmentLayout()
    
    # 创建可视化器
    visualizer = EnvironmentVisualizer(layout)
    
    # 添加几个测试智能体
    visualizer.add_agent("agent1", "小明", "公司")
    visualizer.add_agent("agent2", "小红", "学校")
    visualizer.add_agent("agent3", "小华", "公园")
    
    # 添加一些测试对话
    visualizer.add_dialog("小明", "你好，今天天气真不错！")
    
    # 设置一个定时移动
    def move_agents():
        time.sleep(2)
        visualizer.move_agent("agent1", "公园")
        
        time.sleep(3)
        visualizer.add_dialog("小明", "我到公园了，这里真美！")
        visualizer.add_dialog("小华", "欢迎来到公园，我们一起散步吧！")
        
        time.sleep(2)
        visualizer.move_agent("agent2", "医院")
        
        time.sleep(3)
        visualizer.move_agent("agent3", "餐厅")
        visualizer.move_agent("agent1", "学校")
    
    # 在新线程中运行移动
    import threading
    threading.Thread(target=move_agents, daemon=True).start()
    
    # 运行可视化
    visualizer.run() 