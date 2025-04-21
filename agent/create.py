import os
import random
import shutil
from agent.base_agent import BaseAgent

def clean_environment():
    """清理环境，删除所有智能体及其记忆"""
    # 删除所有history文件夹中的内容
    if os.path.exists("agent/history"):
        for agent_id in os.listdir("agent/history"):
            agent_dir = f"agent/history/{agent_id}"
            if os.path.isdir(agent_dir):
                shutil.rmtree(agent_dir)

def create_new_agents(num_agents=20):
    """创建新的智能体
    
    Args:
        num_agents: 要创建的智能体数量，默认为20
    """
    # 随机生成性别
    genders = []
    for _ in range(num_agents):
        gender = random.choice(["男", "女"])
        genders.append(gender)
    
    # 统计男性和女性数量
    male_count = genders.count("男")
    female_count = genders.count("女")
    
    print(f"需要生成 {male_count} 个男性名字和 {female_count} 个女性名字")
    
    # 不再使用LLM生成名字，直接使用本地名字库
    male_names = []
    female_names = []
    
    # 常见的中文姓氏
    first_names = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴", 
                  "徐", "孙", "朱", "马", "胡", "郭", "林", "何", "高", "梁",
                  "郑", "罗", "宋", "谢", "唐", "韩", "曹", "许", "邓", "萧",
                  "冯", "曾", "程", "蔡", "彭", "潘", "袁", "於", "董", "余",
                  "苏", "叶", "吕", "魏", "蒋", "田", "杜", "丁", "沈", "姜",
                  "范", "江", "傅", "钟", "卢", "汪", "戴", "崔", "任", "陆",
                  "廖", "姚", "方", "金", "邱", "夏", "谭", "韦", "贾", "邹",
                  "石", "熊", "孟", "秦", "阎", "薛", "侯", "雷", "白", "龙",
                  "段", "郝", "孔", "邵", "史", "毛", "常", "万", "顾", "赖"]
    
    # 常见的男性名字部分
    male_second_names = ["伟", "强", "华", "明", "军", "杰", "涛", "超", "刚", "平", 
                        "辉", "勇", "波", "斌", "浩", "鹏", "健", "磊", "建", "龙", 
                        "雷", "雨", "晨", "阳", "宇", "宁", "子", "豪", "志", "文",
                        "天", "翔", "鸿", "森", "思", "智", "涵", "瑞", "锐", "烨",
                        "嘉", "轩", "铭", "峰", "旭", "东", "昊", "奇", "航", "炜",
                        "宏", "胜", "利", "凯", "荣", "桦", "鑫", "博", "岩", "帆"]
    
    # 常见的女性名字部分
    female_second_names = ["芳", "娜", "敏", "静", "丽", "艳", "洁", "燕", "红", "霞", 
                          "倩", "婷", "玲", "娟", "英", "华", "萍", "莉", "文", "芬", 
                          "兰", "珊", "妮", "娥", "琳", "雪", "琴", "璐", "颖", "梅",
                          "玉", "秀", "宁", "瑶", "怡", "婉", "馨", "媛", "嫣", "琦",
                          "晶", "茜", "岚", "瑾", "楠", "曼", "聆", "欣", "悦", "菲",
                          "佳", "涵", "彤", "莹", "雯", "珍", "月", "蓉", "伊", "纯"]
    
    # 生成所需数量的男性名字和女性名字
    for _ in range(male_count):
        first = random.choice(first_names)
        second = random.choice(male_second_names)
        name = f"{first}{second}"
        male_names.append(name)
    
    for _ in range(female_count):
        first = random.choice(first_names)
        second = random.choice(female_second_names)
        name = f"{first}{second}"
        female_names.append(name)
    
    # 确保名字不重复
    male_names = list(dict.fromkeys(male_names))
    female_names = list(dict.fromkeys(female_names))
    
    # 如果去重后名字不够，继续生成
    while len(male_names) < male_count:
        first = random.choice(first_names)
        second = random.choice(male_second_names)
        name = f"{first}{second}"
        if name not in male_names:
            male_names.append(name)
    
    while len(female_names) < female_count:
        first = random.choice(first_names)
        second = random.choice(female_second_names)
        name = f"{first}{second}"
        if name not in female_names:
            female_names.append(name)
    
    # 职业列表
    occupations = ["学生", "教师", "医生", "工程师", "律师", "会计", "销售", "设计师", 
                  "程序员", "记者", "作家", "艺术家", "演员", "音乐家", "厨师", "健身教练",
                  "企业家", "研究员", "公务员", "自由职业者"]
    
    # MBTI类型
    mbti_types = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                 "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
    
    # 分配名字给性别
    agents = []
    male_index = 0
    female_index = 0
    
    for gender in genders:
        if gender == "男":
            name = male_names[male_index]
            male_index += 1
        else:
            name = female_names[female_index]
            female_index += 1
        
        # 生成基本背景信息
        age = random.randint(18, 65)
        occupation = random.choice(occupations)
        mbti = random.choice(mbti_types)
        
        # 教育程度
        education_levels = ["高中", "大专", "本科", "硕士", "博士"]
        education = random.choice(education_levels)
        
        # 家乡（简单的省市组合）
        provinces = ["北京", "上海", "广东", "江苏", "浙江", "山东", "四川", "湖北", "湖南", "河南"]
        cities = ["市", "省"]
        hometown = random.choice(provinces) + random.choice(cities)
        
        # 构建背景字典
        background = {
            "gender": gender,
            "age": age,
            "occupation": occupation,
            "education": education,
            "hometown": hometown
        }
        
        # 创建智能体 - 在创建时传入性别、MBTI和背景信息
        agent_id = str(random.randint(10000, 99999))
        vector_store_dir = f"agent/history/{agent_id}/vector_store"
        
        # 生成外观描述
        appearance = _generate_appearance(gender)
        
        agent = BaseAgent(
            id=agent_id, 
            name=name, 
            gender=gender, 
            age=age,
            mbti=mbti,
            background=background,
            appearance=appearance,
            vector_store_dir=vector_store_dir
        )
        agents.append(agent)
    
    # 保存智能体身份信息
    for agent in agents:
        agent.save_identity()
    
    return agents
    
def _generate_appearance(gender):
    """根据性别生成简单的外观描述"""
    height_desc = ""
    if gender == "男":
        height = random.randint(165, 190)
        if height < 170:
            height_desc = "中等身高"
        elif height < 180:
            height_desc = "较高"
        else:
            height_desc = "很高"
    else:
        height = random.randint(155, 175)
        if height < 160:
            height_desc = "娇小"
        elif height < 170:
            height_desc = "中等身高"
        else:
            height_desc = "较高"
    
    # 发型
    hair_styles = ["短发", "中长发", "长发", "卷发", "直发", "染色的头发"]
    hair_style = random.choice(hair_styles)
    
    # 面部特征
    face_features = ["圆脸", "瓜子脸", "方脸", "鹅蛋脸"]
    face_feature = random.choice(face_features)
    
    # 眼睛特征
    eye_features = ["大眼睛", "明亮的眼睛", "细长的眼睛", "炯炯有神的眼睛"]
    eye_feature = random.choice(eye_features)
    
    # 穿着风格
    clothing_styles = ["休闲风格", "正式风格", "时尚风格", "简约风格", "运动风格", "复古风格"]
    clothing_style = random.choice(clothing_styles)
    
    # 组合描述
    appearance = f"{height_desc}，{hair_style}，{face_feature}，{eye_feature}，喜欢{clothing_style}的穿着。"
    
    return appearance

def load_existing_agents(num_agents=None):
    """加载已存在的智能体
    
    Args:
        num_agents: 要加载的智能体数量，如果为None则加载所有
    """
    agents = []
    saved_agents = BaseAgent.get_all_saved_agents()
    
    if not saved_agents:
        print("没有找到已保存的智能体，将创建新的智能体")
        return create_new_agents(num_agents or 20)
    
    print(f"找到 {len(saved_agents)} 个已保存的智能体")
    
    # 如果指定了数量且小于已有数量，随机选择
    if num_agents and num_agents < len(saved_agents):
        saved_agents = random.sample(saved_agents, num_agents)
    
    for agent_info in saved_agents:
        try:
            agent = BaseAgent.load_from_id(agent_info["id"])
            agents.append(agent)
            print(f"已加载智能体: {agent.name}（{agent.mbti}，{agent.background['gender']}）")
            print(f"外貌: {agent.appearance}")
        except Exception as e:
            print(f"加载智能体 {agent_info['name']} 失败: {str(e)}")
    
    # 如果加载的智能体不够，创建新的补充
    if num_agents and len(agents) < num_agents:
        print(f"已加载智能体数量不足，将创建 {num_agents - len(agents)} 个新智能体补充")
        new_agents = create_new_agents(num_agents - len(agents))
        agents.extend(new_agents)
    
    return agents 