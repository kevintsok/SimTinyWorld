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
                  "企业家", "研究员", "公务员", "自由职业者", "工人", "服务员", "农民", "司机"]
    
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
        
        # 教育程度 - 根据中国实际人口分布加权
        education_levels = ["初中及以下", "高中", "大专", "本科", "硕士", "博士"]
        # 根据中国教育部2022年统计数据和人口分布估算的比例
        education_weights = [15, 35, 25, 20, 4, 1]  # 总和为100
        education = random.choices(education_levels, weights=education_weights, k=1)[0]
        
        # 根据年龄调整教育程度的合理性
        if age < 22 and education in ["硕士", "博士"]:
            education = random.choices(["高中", "大专", "本科"], weights=[40, 35, 25], k=1)[0]
        elif age < 25 and education == "博士":
            education = random.choices(["本科", "硕士"], weights=[70, 30], k=1)[0]
        elif age < 20 and education == "本科":
            education = random.choices(["初中及以下", "高中", "大专"], weights=[20, 50, 30], k=1)[0]
        
        # 职业选择与教育程度关联
        if education == "博士":
            suitable_occupations = ["教师", "医生", "研究员", "企业家", "公务员"]
        elif education == "硕士":
            suitable_occupations = ["教师", "医生", "工程师", "律师", "会计", "程序员", "研究员", "企业家", "公务员"]
        elif education == "本科":
            suitable_occupations = ["教师", "医生", "工程师", "律师", "会计", "销售", "设计师", "程序员", 
                                   "记者", "作家", "企业家", "公务员", "自由职业者"]
        elif education == "大专":
            suitable_occupations = ["销售", "设计师", "程序员", "记者", "作家", "艺术家", "演员", "音乐家",
                                   "厨师", "健身教练", "公务员", "自由职业者", "工人", "服务员", "司机"]
        elif education == "高中":
            suitable_occupations = ["销售", "厨师", "健身教练", "自由职业者", "工人", "服务员", "农民", "司机"]
        else:  # 初中及以下
            suitable_occupations = ["工人", "服务员", "农民", "司机", "自由职业者"]
            
        # 如果是学生，特殊处理
        if age <= 22:
            # 年轻人有较高概率是学生
            if random.random() < 0.6:
                occupation = "学生"
            else:
                occupation = random.choice(suitable_occupations)
        else:
            # 90%概率选择匹配教育程度的职业，10%概率随机选择任意职业（表现社会多样性）
            if random.random() < 0.9:
                occupation = random.choice(suitable_occupations)
            else:
                occupation = random.choice(occupations)
        
        mbti = random.choice(mbti_types)
        
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
        
    # 为每个智能体生成初始长期记忆
    for agent in agents:
        generate_initial_memories(agent)
    
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

def generate_initial_memories(agent):
    """基于智能体的年龄和背景生成初始长期记忆
    
    Args:
        agent: 需要生成记忆的智能体
    """
    # 检查长期记忆文件是否存在且为空
    longterm_file = f"{agent.vector_store_dir}/long.txt"
    
    # 如果文件已存在且不为空，直接返回
    if os.path.exists(longterm_file) and os.path.getsize(longterm_file) > 0:
        return
        
    # 确保目录存在
    os.makedirs(os.path.dirname(longterm_file), exist_ok=True)
    
    # 如果缺少必要的属性，直接返回
    if not hasattr(agent, 'age') or not agent.age or not agent.background or not agent.name:
        print(f"无法为{agent.id}生成初始记忆：缺少年龄或背景信息")
        return
        
    try:
        # 根据年龄确定生成的记忆数量
        age = int(agent.age)
        # 儿童记忆较少，成年人记忆较多
        if age < 18:
            memory_count = max(3, age // 3)  # 6岁=2条，9岁=3条，15岁=5条
        elif age < 30:
            memory_count = 6 + (age - 18) // 2  # 24岁=9条，29岁=11条
        elif age < 50:
            memory_count = 12 + (age - 30) // 3  # 40岁=15条，47岁=17条
        else:
            memory_count = 18 + (age - 50) // 5  # 50岁=18条，65岁=21条
            
        # 最多生成30条记忆
        memory_count = min(memory_count, 30)
        
        # 获取智能体基本信息
        gender = agent.gender or agent.background.get('gender', '未知')
        occupation = agent.background.get('occupation', '未知职业')
        education = agent.background.get('education', '未知')
        hometown = agent.background.get('hometown', '未知')
        
        # 构建提示
        prompt = f"""请为一个虚拟角色生成{memory_count}条长期记忆。

角色信息:
- 姓名: {agent.name}
- 性别: {gender}
- 年龄: {age}岁
- 职业: {occupation}
- 教育程度: {education}
- 家乡: {hometown}
- MBTI性格: {agent.mbti}
- 其他背景: {agent.background.get('description', '')}

生成要求:
1. 生成{memory_count}条重要的长期记忆，这些记忆应该是角色人生中的关键片段
2. 记忆应按时间顺序排列，从早期记忆到近期记忆
3. 包含童年、青少年时期、成年早期、近期等不同人生阶段的记忆
4. 记忆应与角色的职业发展、教育经历、重要人际关系相关
5. 每条记忆应该是1-2句话，具体且有情感色彩
6. 使用第一人称"我"描述这些记忆
7. 符合角色的MBTI性格特点
8. 每条记忆独立成行，不要编号

记忆类型应包括:
- 重要的第一次经历
- 职业上的成就或挫折
- 重要的人际关系发展
- 人生转折点
- 具有情感意义的事件

记忆示例格式:
我5岁时第一次上台表演，紧张得几乎忘记了所有台词，但最后还是完成了演出。
大学三年级时我认识了我的挚友李明，他帮我度过了学业最困难的时期。
我28岁获得了第一次工作晋升，那天晚上我兴奋得几乎一夜未眠。

注意:
- 不要包含任何与输出格式无关的文字
- 直接输出记忆内容，每条一行
- 确保记忆符合角色的年龄、背景和性格
"""

        # 获取LLM生成的记忆
        memories = agent._generate_with_llm(prompt)
        
        # 如果生成成功
        if memories and memories.strip():
            # 分割成单独的记忆条目
            memory_items = [m.strip() for m in memories.split('\n') if m.strip()]
            
            # 过滤掉可能的编号和无关信息
            filtered_memories = []
            for memory in memory_items:
                # 移除可能的编号前缀
                if memory and memory[0].isdigit() and len(memory) > 2 and memory[1:3] in ['. ', '、', '：', ': ']:
                    memory = memory[3:].strip()
                
                # 如果记忆不以"我"开头，添加前缀
                if memory and not memory.startswith('我'):
                    memory = f"我{memory}"
                    
                if memory:  # 确保记忆不为空
                    filtered_memories.append(memory)
            
            # 将记忆保存到长期记忆
            if filtered_memories:
                with open(longterm_file, "w", encoding="utf-8") as f:
                    f.write('\n'.join(filtered_memories))
                print(f"为{agent.name}生成了{len(filtered_memories)}条初始长期记忆")
                
                # 更新智能体的长期记忆
                agent.long_term_memory = filtered_memories
                
                # 更新向量存储
                agent._update_vector_store()
                return
        
        # 如果生成失败，使用基础记忆
        generate_basic_memories(agent)
            
    except Exception as e:
        print(f"生成初始长期记忆时出错: {e}")
        generate_basic_memories(agent)

def generate_basic_memories(agent):
    """生成基础的长期记忆，当LLM生成失败时使用
    
    Args:
        agent: 需要生成记忆的智能体
    """
    # 检查长期记忆文件路径
    longterm_file = f"{agent.vector_store_dir}/long.txt"
    
    # 基于年龄和背景生成基础记忆
    try:
        age = int(agent.age)
        gender = agent.gender or agent.background.get('gender', '男')
        occupation = agent.background.get('occupation', '职员')
        
        basic_memories = []
        
        # 童年记忆
        if age > 5:
            basic_memories.append(f"我5岁时第一次上学，感到既兴奋又紧张。")
        if age > 10:
            basic_memories.append(f"我10岁时获得了第一个学习奖项，父母非常自豪。")
            
        # 青少年记忆
        if age > 15:
            basic_memories.append(f"我初中时结交了一些好朋友，我们经常一起玩耍和学习。")
        if age > 18:
            basic_memories.append(f"我高中毕业那天，和同学们一起庆祝，充满对未来的憧憬。")
            
        # 早期成人记忆
        if age > 22:
            basic_memories.append(f"我大学期间努力学习专业知识，为未来的职业生涯打下基础。")
        if age > 25:
            basic_memories.append(f"我第一份工作是{occupation}，刚开始工作时充满热情但也面临挑战。")
            
        # 职业相关记忆
        if age > 30:
            basic_memories.append(f"我在工作中经历了第一次晋升，认识到专业能力的重要性。")
        if age > 35:
            basic_memories.append(f"我在工作中遇到了一些困难，但通过努力最终克服了。")
            
        # 中年记忆
        if age > 40:
            basic_memories.append(f"随着年龄增长，我开始重新审视生活的优先级，更注重生活质量。")
        if age > 50:
            basic_memories.append(f"步入中年后，我开始关注健康问题，调整了生活习惯。")
            
        # 近期记忆
        basic_memories.append(f"最近几年，我尝试在工作和生活中寻找平衡，学会享受当下。")
        basic_memories.append(f"我一直在思考如何能够在我的领域有所建树，留下一些成就。")
        
        # 保存基础记忆
        with open(longterm_file, "w", encoding="utf-8") as f:
            f.write('\n'.join(basic_memories))
        print(f"为{agent.name}生成了{len(basic_memories)}条基础长期记忆")
        
        # 更新智能体的长期记忆
        agent.long_term_memory = basic_memories
        
        # 更新向量存储
        agent._update_vector_store()
        
    except Exception as e:
        print(f"生成基础记忆时出错: {e}")
        # 创建空记忆文件
        with open(longterm_file, "w", encoding="utf-8") as f:
            f.write("")
        agent.long_term_memory = []

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
            
            # 确保agent有vector_store_dir属性
            if not hasattr(agent, 'vector_store_dir') or not agent.vector_store_dir:
                agent.vector_store_dir = f"agent/history/{agent.id}/vector_store"
                os.makedirs(agent.vector_store_dir, exist_ok=True)
            
            # 确保加载的智能体也有初始长期记忆
            generate_initial_memories(agent)
        except Exception as e:
            print(f"加载智能体 {agent_info['name']} 失败: {str(e)}")
    
    # 如果加载的智能体不够，创建新的补充
    if num_agents and len(agents) < num_agents:
        print(f"已加载智能体数量不足，将创建 {num_agents - len(agents)} 个新智能体补充")
        new_agents = create_new_agents(num_agents - len(agents))
        agents.extend(new_agents)
    
    return agents 