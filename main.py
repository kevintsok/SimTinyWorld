import os
import time
import argparse
import shutil
from agent.base_agent import BaseAgent
from environment.world import World
from environment.environment_descriptions import EnvironmentDescriptions
import random
import json
from typing import List
from agent.interact import initiate_conversation

# 添加LLM引擎验证器
from llm_engine.engine_verifier import EngineVerifier

def verify_llm_engines():
    """验证LLM引擎状态，并显示结果"""
    print("\n正在验证LLM引擎状态...")
    verifier = EngineVerifier()
    verifier.verify_all_engines()
    verifier.display_status()
    
    # 获取可用的引擎
    available_engines = verifier.get_available_engines()
    mock_engines = verifier.get_engines_in_mock_mode()
    
    if not available_engines and not mock_engines:
        print("\n警告: 没有可用的LLM引擎，程序可能无法正常运行。")
        print("请检查API密钥配置和网络连接。")
        # 询问用户是否仍要继续
        response = input("是否仍要继续运行程序? (y/n): ")
        if response.lower() != 'y':
            print("程序退出。")
            exit(1)
    elif not available_engines and mock_engines:
        print("\n注意: 所有LLM引擎都处于模拟模式。智能体将使用预设的回复，而不是真实的LLM响应。")
        # 询问用户是否仍要继续
        response = input("是否仍要继续运行程序? (y/n): ")
        if response.lower() != 'y':
            print("程序退出。")
            exit(1)
    
    return verifier.get_first_available_engine()

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
    # 从llm_engine import get_llm_engine
    
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
        
        # 创建智能体 - 在创建时传入性别
        agent = BaseAgent(name, gender=gender)
        agents.append(agent)
    
    # 保存智能体身份信息
    for agent in agents:
        agent.save_identity()
    
    return agents

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

def run_simulation(agents, rounds=5, visual_mode=False, max_conversation_participants=4, environment_init=False, location_count=5):
    """
    运行智能体模拟
    
    参数:
    agents: 智能体列表
    rounds: 模拟轮数
    visual_mode: 是否启用可视化模式
    max_conversation_participants: 一次对话最多参与者数量
    environment_init: 是否重新初始化环境描述
    location_count: 生成的地点数量
    """
    # 初始化环境描述
    env_descriptions = EnvironmentDescriptions()
    env_descriptions.initialize_environment(force=environment_init)
    
    # 创建世界实例
    world = World(visual_mode=visual_mode, location_count=location_count)
    
    # 获取所有可用位置
    available_locations = list(world.locations.keys())
    
    # 将智能体添加到世界的不同位置（尽量平均分配）
    for i, agent in enumerate(agents):
        # 循环使用位置，确保每个位置都有智能体
        location = available_locations[i % len(available_locations)]
        world.add_agent(agent, location)
        print(f"{agent.name}（{agent.mbti}，{agent.background['gender']}）被放置在{location}")
        print(f"外貌: {agent.appearance}")
        print(f"财富状态: 时间:{agent.wealth['time']:.2f}, 社交:{agent.wealth['social']:.2f}, 健康:{agent.wealth['health']:.2f}, 精神:{agent.wealth['mental']:.2f}, 金钱:{agent.wealth['money']:.2f}元")
        
        # 记录初始位置到短期记忆中
        agent.add_memory(f"我现在在{location}。{world.locations[location].description}")
    
    try:
        # 计算每天的轮数和总天数
        rounds_per_day = 5  # 每天默认5轮
        total_days = (rounds + rounds_per_day - 1) // rounds_per_day  # 向上取整，确保所有轮数都被执行
        
        # 模拟多天的活动
        current_round = 0
        for day in range(total_days):
            print(f"\n=== 第{day+1}天开始 ===")
            
            # 在新的一天开始时，让所有智能体制定计划
            print("\n=== 智能体们正在制定计划 ===")
            
            # 准备位置描述字典
            location_descriptions = {}
            for loc_name in world.locations:
                location_descriptions[loc_name] = world.locations[loc_name].description
            
            # 让每个智能体制定计划
            for agent in agents:
                print(f"{agent.name} 正在制定今日计划...")
                agent.plan(
                    available_locations=list(world.locations.keys()),
                    location_descriptions=location_descriptions,
                    max_rounds=rounds_per_day  # 每天的最大轮数
                )
                
                # 打印计划摘要
                if agent.daily_plan:
                    plan_summary = f"{agent.name} 的今日计划："
                    for i, item in enumerate(agent.daily_plan):
                        plan_summary += f"\n{i+1}. {item['location']}({item['duration']}轮): {item['activity']} ({item['status']})"
                    print(plan_summary)
            
            print("=== 所有智能体都已制定计划 ===\n")
            
            # 计算当天可执行的轮数（不超过剩余总轮数）
            day_rounds = min(rounds_per_day, rounds - current_round)
            
            # 模拟当天的轮次
            for round_in_day in range(day_rounds):
                current_round += 1
                print(f"\n=== 第{day+1}天 第{round_in_day+1}轮活动开始（总第{current_round}轮）===")
                
                # 根据计划移动智能体，而不是随机移动
                for agent in agents:
                    # 获取智能体当前位置
                    current_location = None
                    for loc_name, loc in world.locations.items():
                        if agent.id in loc.current_agents:
                            current_location = loc_name
                            break
                    
                    # 获取计划中的下一个位置
                    next_location = agent.get_next_planned_location()
                    
                    # 如果有计划的下一个位置，并且与当前位置不同，尝试移动
                    if next_location and next_location != current_location:
                        # 检查是否可以直接移动（是否相连）
                        connected_locations = world.get_connected_locations(current_location)
                        
                        if next_location in connected_locations:
                            # 直接移动到目标位置
                            if world.move_agent(agent.id, next_location):
                                print(f"{agent.name}({agent.status})从{current_location}移动到了{next_location}")
                                # 记录移动到短期记忆
                                agent.add_memory(f"我从{current_location}移动到了{next_location}。{world.locations[next_location].description}")
                        else:
                            # 如果目标位置不直接相连，找到一条路径
                            # 简单方法：选择一个朝着目标方向的位置
                            # 这里可以实现更复杂的寻路算法
                            if connected_locations:
                                # 随机选择一个位置朝着目标位置移动
                                random_next = random.choice(connected_locations)
                                if world.move_agent(agent.id, random_next):
                                    print(f"{agent.name}({agent.status})从{current_location}移动到了{random_next}，正在前往{next_location}")
                                    # 记录移动到短期记忆
                                    agent.add_memory(f"我从{current_location}移动到了{random_next}，正在前往{next_location}。{world.locations[random_next].description}")
                    else:
                        # 如果已经在计划的位置或者没有计划，则停留在当前位置
                        if next_location and next_location == current_location:
                            plan_item = agent.daily_plan[agent.current_plan_index]
                            print(f"{agent.name}({agent.status})在{current_location}停留，{plan_item['activity']}")
                            agent.add_memory(f"我在{current_location}进行了活动：{plan_item['activity']}")
                        
                    # 更新计划进度
                    agent.update_plan_progress()
                
                # 打印每个地点的智能体情况
                print("\n=== 当前各地点智能体分布 ===")
                for location_name, location in world.locations.items():
                    agents_at_location = world.get_agents_at_location(location_name)
                    if agents_at_location:
                        agent_names = [f"{agent.name}({agent.status})" for agent in agents_at_location]
                        print(f"{location_name}: {', '.join(agent_names)} (共{len(agents_at_location)}人)")
                    else:
                        print(f"{location_name}: 无人")
                
                # 检查每个位置的智能体互动
                for location_name in world.locations:
                    agents_at_location = world.get_agents_at_location(location_name)
                    
                    # 如果当前位置有多个智能体，可以进行对话
                    if len(agents_at_location) > 1:
                        print(f"\n在{location_name}的智能体们开始互动：")
                        
                        # 智能体分组对话
                        conversation_groups = []
                        remaining_agents = agents_at_location.copy()
                        
                        # 优先将外向型智能体作为对话发起者
                        sorted_remaining = sorted(remaining_agents, key=lambda a: 0 if a.mbti.startswith('E') else 1)
                        
                        while len(sorted_remaining) >= 2:
                            # 确定这一组的大小
                            max_possible_size = min(len(sorted_remaining), max_conversation_participants)
                            if max_possible_size <= 2:
                                group_size = 2
                            else:
                                # 根据外向型智能体比例调整组大小概率
                                extroverts = sum(1 for a in sorted_remaining[:max_possible_size] if a.mbti.startswith('E'))
                                extrovert_ratio = extroverts / max_possible_size
                                
                                if extrovert_ratio > 0.5:  # 外向型智能体较多，更可能形成大组
                                    # 偏向较大组
                                    size_weights = [0.1, 0.2, 0.3, 0.4][:max_possible_size-1]
                                else:  # 内向型智能体较多，更可能形成小组
                                    # 偏向较小组
                                    size_weights = [0.4, 0.3, 0.2, 0.1][:max_possible_size-1]
                                    
                                # 归一化权重
                                total = sum(size_weights)
                                size_weights = [w/total for w in size_weights]
                                
                                # 根据权重随机选择组大小
                                sizes = list(range(2, max_possible_size+1))
                                group_size = random.choices(sizes, weights=size_weights, k=1)[0]
                            
                            # 随机选择智能体组成对话组（保证第一个是外向型，如果有的话）
                            if sorted_remaining and sorted_remaining[0].mbti.startswith('E'):
                                # 第一个必须是外向型
                                first_member = sorted_remaining[0]
                                other_members = random.sample(sorted_remaining[1:], min(group_size-1, len(sorted_remaining)-1))
                                group = [first_member] + other_members
                            else:
                                # 没有外向型，完全随机
                                group = random.sample(sorted_remaining, min(group_size, len(sorted_remaining)))
                                
                            conversation_groups.append(group)
                            
                            # 从剩余智能体中移除已分配的智能体
                            for agent in group:
                                sorted_remaining.remove(agent)
                        
                        # 处理每个对话组
                        for group_idx, participants in enumerate(conversation_groups):
                            # 显示对话组信息
                            participant_info = ", ".join([f"{a.name}({a.mbti}，{a.background['gender']})" for a in participants])
                            print(f"\n对话组 {group_idx + 1}：{participant_info}")
                            
                            # 获取环境描述
                            environment_desc = env_descriptions.get_description(location_name)
                            
                            # 生成可能的对话话题
                            potential_topics = env_descriptions.get_topics(location_name)
                            suggested_topic = random.choice(potential_topics)
                            
                            # 使用interact模块进行对话
                            initiate_conversation(
                                participants=participants,
                                location_name=location_name,
                                environment_desc=environment_desc,
                                world=world,
                                suggested_topic=suggested_topic
                            )
                
                # 使用LLM引擎判断是否需要更新智能体的财富值
                update_agents_wealth(agents, world)
                
                # 更新世界可视化，仅在可视化模式下
                if visual_mode:
                    for _ in range(10):  # 更新多次以确保动画流畅
                        world.update_world()
                        time.sleep(0.1)
                
                time.sleep(1)  # 暂停一下，让输出更容易阅读
            
            # 一天结束时，所有智能体进入睡眠模式，整理记忆
            print("\n=== 第{day+1}天结束，智能体进入睡眠状态 ===")
            for agent in agents:
                print(f"{agent.name} 正在整理今天的记忆和反思计划完成情况...")
                agent.sleep()
            print("=== 所有智能体都已完成记忆整理 ===\n")
        
        # 模拟结束前持续更新一段时间，仅在可视化模式下
        if visual_mode:
            print("\n模拟结束，按ESC键退出可视化...")
            for _ in range(50):  # 更新一段时间以便查看最终状态
                if not world.update_world():
                    break
                time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n模拟被用户中断")
    
    # 确保可视化器正确关闭，仅在可视化模式下
    if visual_mode and world.visualizer:
        world.visualizer.close()

# 新增函数：更新智能体财富值
def update_agents_wealth(agents, world):
    """
    根据智能体的活动和交互情况，判断并更新其财富值
    
    参数:
    agents: 所有智能体列表
    world: 世界实例
    """
    print("\n=== 更新智能体财富值 ===")
    
    # 为每个智能体获取最近的记忆和活动
    for agent in agents:
        # 如果没有最近记忆，跳过
        if not agent.short_term_memory:
            continue
            
        # 获取最近三条记忆
        recent_memories = agent.short_term_memory[-3:] if len(agent.short_term_memory) >= 3 else agent.short_term_memory
        recent_activities = "\n".join(recent_memories)
        
        # 获取当前位置
        current_location = None
        for loc_name, loc in world.locations.items():
            if agent.id in loc.current_agents:
                current_location = loc_name
                break
                
        if not current_location:
            continue
            
        # 构建提示
        prompt = f"""作为财富评估器，请分析以下智能体的最近活动，并判断是否需要更新其财富值。

智能体信息:
- 姓名: {agent.name}
- 性别: {agent.background['gender']}
- 年龄: {agent.background['age']}
- 职业: {agent.background['occupation']}
- MBTI性格: {agent.mbti}
- 当前位置: {current_location}

当前财富状态:
- 时间财富: {agent.wealth['time']:.2f} (-1.0到1.0，越高表示自由时间越多)
- 社交财富: {agent.wealth['social']:.2f} (-1.0到1.0，越高表示社交资源越丰富)
- 健康财富: {agent.wealth['health']:.2f} (-1.0到1.0，越高表示越健康)
- 精神财富: {agent.wealth['mental']:.2f} (-1.0到1.0，越高表示精神状态越好)
- 金钱财富: {agent.wealth['money']:.2f}元

最近活动:
{recent_activities}

请分析这些活动是否会影响智能体的财富值，并给出调整建议。例如:
- 如果进行了运动或户外活动，健康财富可能增加
- 如果进行了社交活动，社交财富可能增加
- 如果工作或学习，时间财富可能减少，但精神财富可能增加
- 如果购物或消费，金钱财富可能减少

只返回一个JSON格式的调整数据，格式如下:
{{
  "time": 0.1,  // 变化值，正数为增加，负数为减少
  "social": 0.2,
  "health": 0.0,  // 0表示不变
  "mental": -0.1,
  "money": -50.0  // 金钱的绝对变化值
}}
"""

        try:
            # 获取LLM的分析结果
            response = agent.llm_engine.generate(prompt)
            
            # 解析JSON
            try:
                import json
                import re
                
                # 找到JSON部分并解析
                json_match = re.search(r'\{.*\}', response.replace('\n', ''), re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    changes = json.loads(json_str)
                    
                    # 提取变化值
                    time_change = float(changes.get("time", 0))
                    social_change = float(changes.get("social", 0))
                    health_change = float(changes.get("health", 0))
                    mental_change = float(changes.get("mental", 0))
                    money_change = float(changes.get("money", 0))
                    
                    # 确保变化在合理范围内
                    time_change = max(min(time_change, 0.2), -0.2)  # 限制单次变化幅度
                    social_change = max(min(social_change, 0.2), -0.2)
                    health_change = max(min(health_change, 0.2), -0.2)
                    mental_change = max(min(mental_change, 0.2), -0.2)
                    money_change = max(min(money_change, 1000), -1000)  # 限制金钱变化
                    
                    # 应用变化
                    old_wealth = {k: v for k, v in agent.wealth.items()}  # 保存旧值用于比较
                    
                    # 更新财富值，确保在合法范围内
                    agent.wealth["time"] = max(min(agent.wealth["time"] + time_change, 1.0), -1.0)
                    agent.wealth["social"] = max(min(agent.wealth["social"] + social_change, 1.0), -1.0)
                    agent.wealth["health"] = max(min(agent.wealth["health"] + health_change, 1.0), -1.0)
                    agent.wealth["mental"] = max(min(agent.wealth["mental"] + mental_change, 1.0), -1.0)
                    agent.wealth["money"] = max(agent.wealth["money"] + money_change, 0.0)  # 金钱最小为0
                    
                    # 如果有显著变化，输出提示
                    if (abs(time_change) > 0.05 or abs(social_change) > 0.05 or 
                        abs(health_change) > 0.05 or abs(mental_change) > 0.05 or 
                        abs(money_change) > 10.0):
                        
                        print(f"{agent.name} 的财富发生变化:")
                        
                        if abs(time_change) > 0.05:
                            change_desc = "增加" if time_change > 0 else "减少"
                            print(f"  - 时间财富 {old_wealth['time']:.2f} -> {agent.wealth['time']:.2f} ({change_desc})")
                            
                        if abs(social_change) > 0.05:
                            change_desc = "增加" if social_change > 0 else "减少"
                            print(f"  - 社交财富 {old_wealth['social']:.2f} -> {agent.wealth['social']:.2f} ({change_desc})")
                            
                        if abs(health_change) > 0.05:
                            change_desc = "增加" if health_change > 0 else "减少"
                            print(f"  - 健康财富 {old_wealth['health']:.2f} -> {agent.wealth['health']:.2f} ({change_desc})")
                            
                        if abs(mental_change) > 0.05:
                            change_desc = "增加" if mental_change > 0 else "减少"
                            print(f"  - 精神财富 {old_wealth['mental']:.2f} -> {agent.wealth['mental']:.2f} ({change_desc})")
                            
                        if abs(money_change) > 10.0:
                            change_desc = "增加" if money_change > 0 else "减少"
                            print(f"  - 金钱财富 {old_wealth['money']:.2f} -> {agent.wealth['money']:.2f}元 ({change_desc})")
            except Exception as e:
                print(f"解析财富变化数据时出错: {e}")
                
        except Exception as e:
            print(f"更新{agent.name}的财富时出错: {e}")
    
    print("=== 财富更新完成 ===\n")

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="智能体模拟程序")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--mode", choices=["new", "continue"], default="new",
                      help="运行模式: new(重新开始) 或 continue(继续)")
    mode_group.add_argument("--continue", "-c", action="store_true", dest="continue_mode",
                      help="继续模式，加载现有智能体")
    parser.add_argument("--rounds", type=int, default=5,
                      help="模拟轮数")
    parser.add_argument("--visual", action="store_true", default=False,
                      help="是否使用可视化模式，默认为终端模式")
    parser.add_argument("--agents", type=int, default=20,
                      help="智能体数量，默认为20")
    parser.add_argument("--max-participants", type=int, default=4,
                      help="一次对话最多参与者数量，默认为4")
    parser.add_argument("--reinit-env", action="store_true", default=False,
                      help="是否重新初始化环境描述，默认为否")
    parser.add_argument("--locations", type=int, default=5,
                      help="生成的地点数量，默认为5个")
    parser.add_argument("--skip-verify", action="store_true", default=False,
                      help="跳过LLM引擎验证")
    parser.add_argument("--engine", type=str, default=None,
                      help="指定使用的LLM引擎类型（qwen, openai, deepseek）")
    
    args = parser.parse_args()
    
    # 处理模式设置 - 如果使用了--continue/-c参数，将mode设为"continue"
    if args.continue_mode:
        args.mode = "continue"
    
    print(f"以 {args.mode} 模式启动模拟...")
    print(f"使用{'可视化' if args.visual else '终端'}模式")
    print(f"智能体数量: {args.agents}")
    print(f"地点数量: {args.locations}")
    print(f"对话最大参与者数量: {args.max_participants}")
    
    # 验证LLM引擎状态
    if not args.skip_verify:
        default_engine = verify_llm_engines()
        
        # 如果用户没有指定引擎，使用第一个可用的引擎
        if not args.engine and default_engine:
            args.engine = default_engine
            print(f"\n自动选择LLM引擎: {args.engine}")
    
    # 如果指定了引擎，设置环境变量
    if args.engine:
        os.environ["DEFAULT_LLM_ENGINE"] = args.engine
    
    if args.mode == "new":
        # 重新开始模式：清理环境并创建新的智能体
        print("清理环境...")
        clean_environment()
        print(f"创建 {args.agents} 个新的智能体...")
        agents = create_new_agents(args.agents)
    else:
        # 继续模式：加载已存在的智能体
        print("加载现有智能体...")
        agents = load_existing_agents(args.agents)
    
    # 运行模拟
    run_simulation(agents, rounds=args.rounds, visual_mode=args.visual, 
                  max_conversation_participants=args.max_participants,
                  environment_init=args.reinit_env,
                  location_count=args.locations)
    
    print("\n模拟结束")

if __name__ == "__main__":
    main() 

"""
参数说明文档：

max_conversation_participants参数介绍
-----------------------------
此参数控制对话组中最大可能的参与人数。默认值为4。

功能：
1. 限制每个对话组的最大人数，使对话更加自然和易于管理
2. 影响智能体分组策略
3. 依据MBTI性格类型（外向E/内向I）动态调整组大小

当场景中的智能体数量过多时，特别有用。较小的值（2-3）会使对话更加简短和聚焦，
较大的值（5+）会导致更复杂的多人互动。

命令行用法示例：
python main.py --max-participants 6  # 设置最大对话人数为6人
""" 