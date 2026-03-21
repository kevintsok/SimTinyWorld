import os
import json
from llm_engine import get_llm_engine

class EnvironmentDescriptions:
    """
    管理环境描述的生成和读取
    """
    def __init__(self, descriptions_dir="environment/descriptions"):
        """初始化环境描述管理器
        
        Args:
            descriptions_dir: 环境描述文件存储的目录
        """
        self.descriptions_dir = descriptions_dir
        self.default_locations = [
            "公司", "公园", "学校", "医院", "餐厅", "商场", "图书馆", "健身房"
        ]
        self.descriptions = {}
        self.topics = {}
        
        # 确保目录存在
        os.makedirs(descriptions_dir, exist_ok=True)
    
    def load_descriptions(self):
        """从文件加载环境描述"""
        descriptions_file = os.path.join(self.descriptions_dir, "environment_descriptions.txt")
        if not os.path.exists(descriptions_file):
            return False
        
        try:
            with open(descriptions_file, 'r', encoding='utf-8') as f:
                self.descriptions = json.loads(f.read())
            return True
        except Exception as e:
            print(f"加载环境描述文件失败: {e}")
            return False
    
    def load_topics(self):
        """从文件加载对话话题"""
        topics_file = os.path.join(self.descriptions_dir, "environment_topics.txt")
        if not os.path.exists(topics_file):
            return False
        
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                self.topics = json.loads(f.read())
            return True
        except Exception as e:
            print(f"加载对话话题文件失败: {e}")
            return False
    
    def generate_descriptions(self):
        """使用LLM生成环境描述"""
        print("正在生成环境描述...")
        llm = get_llm_engine()
        
        # 构建提示词
        prompt = f"""
请为以下地点生成详细、生动的环境描述，每个描述应当包含环境的视觉、听觉、嗅觉等感官信息，以及可能的氛围和活动。
每个描述应当在100-200字之间。

地点列表：
{', '.join(self.default_locations)}

请以JSON格式输出，键为地点名称，值为对应的环境描述。不要包含任何其他文字说明，只输出JSON。
例如：
{{
  "地点1": "这里是地点1的环境描述...",
  "地点2": "这里是地点2的环境描述..."
}}
"""
        
        try:
            response = llm.generate(prompt)
            
            # 检查响应是否为None或空
            if response is None or not response.strip():
                print("LLM返回空响应，使用默认环境描述")
                raise ValueError("空响应")
            
            # 尝试提取JSON部分
            try:
                # 查找JSON开始和结束的位置
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    self.descriptions = json.loads(json_str)
                else:
                    raise ValueError("未找到有效的JSON内容")
                
                # 确保所有默认地点都有描述
                for location in self.default_locations:
                    if location not in self.descriptions:
                        self.descriptions[location] = f"一个{location}环境，周围的人们正在进行各种活动。"
                return True
            except json.JSONDecodeError as je:
                print(f"JSON解析错误: {je}, 响应内容: {response[:100]}...")
                raise
        except Exception as e:
            print(f"解析环境描述失败: {e}")
            # 使用默认描述
            self.descriptions = {location: f"一个{location}环境，周围的人们正在进行各种活动。" for location in self.default_locations}
            return False
    
    def generate_topics(self):
        """使用LLM生成每个环境的对话话题"""
        print("正在生成对话话题...")
        llm = get_llm_engine()
        
        # 构建提示词
        prompt = f"""
请为以下地点生成5个适合在该环境下讨论的话题。
每个话题应该简洁明了，只需2-5个字。

地点列表：
{', '.join(self.default_locations)}

请以JSON格式输出，键为地点名称，值为包含5个话题的数组。
"""
        
        try:
            response = llm.generate(prompt)
            
            # 检查响应是否为None或空
            if response is None or not response.strip():
                print("LLM返回空响应，使用默认话题")
                raise ValueError("空响应")
                
            # 尝试解析JSON响应
            self.topics = json.loads(response)
            # 确保所有默认地点都有话题
            for location in self.default_locations:
                if location not in self.topics:
                    self.topics[location] = ["周围环境", "日常生活", "个人兴趣", "社交活动", "未来计划"]
            return True
        except Exception as e:
            print(f"解析对话话题失败: {e}")
            # 创建默认话题
            self.topics = {
                "公司": ["工作压力", "办公室政治", "职业发展", "项目进度", "工作环境"],
                "公园": ["自然风光", "户外活动", "天气状况", "放松方式", "城市绿化"],
                "学校": ["学习方法", "课程内容", "校园活动", "教育理念", "学生生活"],
                "医院": ["健康问题", "医疗服务", "养生之道", "就医经历", "医患关系"],
                "餐厅": ["美食推荐", "饮食习惯", "口味偏好", "餐厅环境", "烹饪技巧"],
                "商场": ["购物体验", "商品质量", "促销活动", "消费观念", "时尚潮流"],
                "图书馆": ["阅读习惯", "图书推荐", "知识获取", "安静环境", "学习氛围"],
                "健身房": ["健身计划", "运动方式", "健康生活", "体型管理", "运动装备"]
            }
            return True
    
    def save_descriptions(self):
        """将环境描述保存到文件"""
        descriptions_file = os.path.join(self.descriptions_dir, "environment_descriptions.txt")
        try:
            with open(descriptions_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.descriptions, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"保存环境描述文件失败: {e}")
            return False
    
    def save_topics(self):
        """将对话话题保存到文件"""
        topics_file = os.path.join(self.descriptions_dir, "environment_topics.txt")
        try:
            with open(topics_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.topics, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"保存对话话题文件失败: {e}")
            return False
    
    def get_description(self, location):
        """获取指定地点的环境描述
        
        Args:
            location: 地点名称
            
        Returns:
            str: 环境描述
        """
        return self.descriptions.get(location, f"一个{location}环境，周围的人们正在进行各种活动。")
    
    def get_location_desc(self, location):
        """获取指定地点的环境描述（get_description的别名）
        
        Args:
            location: 地点名称
            
        Returns:
            str: 环境描述
        """
        return self.get_description(location)
    
    def get_topics(self, location):
        """获取指定地点的对话话题
        
        Args:
            location: 地点名称
            
        Returns:
            list: 话题列表
        """
        return self.topics.get(location, ["周围环境", "日常生活", "个人兴趣", "社交活动", "未来计划"])
    
    def initialize_environment(self, force=False):
        """初始化环境描述和话题
        
        Args:
            force: 是否强制重新生成
            
        Returns:
            bool: 是否初始化成功
        """
        # 检查文件是否存在，如不存在或强制重新生成则生成新的
        descriptions_exist = self.load_descriptions()
        topics_exist = self.load_topics()
        
        if (not descriptions_exist or not topics_exist or force):
            # 生成新的环境描述和话题
            self.generate_descriptions()
            self.generate_topics()
            
            # 保存到文件
            self.save_descriptions()
            self.save_topics()
            return True
        
        return True 