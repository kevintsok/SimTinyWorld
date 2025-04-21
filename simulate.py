import os
import time
import random
import json
from agent.base_agent import BaseAgent
from environment.world import World
from environment.environment_descriptions import EnvironmentDescriptions
from agent.interact import initiate_conversation

def run_dialogue(agents, location, round_index, max_participants=4):
    """运行一轮对话，让智能体之间交互
    
    Args:
        agents: 参与对话的智能体列表
        location: 对话发生的位置
        round_index: 当前轮次索引
        max_participants: 最大参与者数量，默认为4
    """
    # 如果智能体数量大于max_participants，随机选择max_participants个
    if len(agents) > max_participants:
        participating_agents = random.sample(agents, max_participants)
    else:
        participating_agents = agents.copy()
    
    # 如果只有一个智能体，不进行对话
    if len(participating_agents) < 2:
        solo_agent = participating_agents[0]
        solo_thought = f"我在{location}，周围没有其他人，感到{solo_agent.mood['description']}。"
        solo_agent.add_memory(solo_thought)
        # 更新独自一人时的心情
        if random.random() < 0.7:  # 70%的概率更新心情
            if solo_agent.mbti.startswith('E'):  # 外向型独处会降低心情
                solo_agent.update_mood('solitude', 0.1, f"在{location}独自一人")
            else:  # 内向型独处可能提升心情
                solo_agent.update_mood('solitude', 0.1, f"在{location}享受独处时光")
        return

    # 为每轮对话选择一个起始发言者
    last_speaker = random.choice(participating_agents)
    
    # 初始提示，开始对话
    dialogue_context = f"我们现在在{location}。"
    query = f"我们大家现在在{location}，有谁想开始对话？"
    
    # 记录已经说过再见的智能体
    said_goodbye = set()
    
    # 对话轮次
    conversation_rounds = min(random.randint(3, 6), len(participating_agents) * 2)
    
    for i in range(conversation_rounds):
        # 让上一个发言者选择下一个发言者（如果不是第一轮）
        if i > 0:
            # 筛选未说再见的智能体
            available_agents = [a for a in participating_agents if a.id not in said_goodbye]
            
            # 如果没有可用的智能体，结束对话
            if not available_agents:
                break
                
            # 获取上一个发言者的回复中提到的智能体
            mentioned_agents = []
            for agent in available_agents:
                if agent.id != last_speaker.id and agent.name in response:
                    mentioned_agents.append(agent)
            
            # 如果有提到的智能体，80%的概率选择其中一个作为下一个发言者
            if mentioned_agents and random.random() < 0.8:
                next_speaker = random.choice(mentioned_agents)
            else:
                # 随机选择一个非上一个发言者的智能体
                next_speaker_candidates = [a for a in available_agents if a.id != last_speaker.id]
                if next_speaker_candidates:
                    next_speaker = random.choice(next_speaker_candidates)
                else:
                    # 如果没有其他智能体，让当前智能体继续说
                    next_speaker = last_speaker
        else:
            # 第一轮随机选择
            next_speaker = random.choice(participating_agents)
            
        # 构建对话提示
        if i == 0:
            query_for_agent = f"我们大家现在在{location}。作为对话的第一个发言者，请友好地开始对话。"
        else:
            others = [a.name for a in participating_agents if a.id != next_speaker.id]
            others_str = "、".join(others)
            query_for_agent = f"{last_speaker.name}对我说：'{response}' 我们现在在{location}，还有{others_str}也在场。"
        
        # 获取下一个发言者的回复
        try:
            response = next_speaker.respone(query_for_agent)
        except Exception as e:
            print(f"Error getting response from {next_speaker.name}: {e}")
            response = f"（看起来有些犹豫，没有说话）"
        
        # 打印对话内容
        print(f"{next_speaker.name} ({next_speaker.status}, {next_speaker.mood['description']}): {response}")
        
        # 更新对话记忆
        memory_text = f"在{location}，我对大家说：'{response}'"
        next_speaker.add_memory(memory_text)
        
        # 为其他参与者添加听到的对话记忆
        for agent in participating_agents:
            if agent.id != next_speaker.id:
                agent_memory = f'在{location}，{next_speaker.name}说："{response}"'
                agent.add_memory(agent_memory)
        
        # 更新发言者的心情
        # 对话后根据内容和性格更新心情
        response_lower = response.lower()
        # 检测对话情绪
        mood_change_reason = ""
        if "再见" in response_lower or "拜拜" in response_lower or "走了" in response_lower:
            said_goodbye.add(next_speaker.id)
            mood_change_reason = f"要离开{location}的对话"
        elif any(word in response_lower for word in ["高兴", "开心", "愉快", "喜欢", "好玩"]):
            next_speaker.update_mood('positive_conversation', 0.15, f"在{location}进行愉快的对话")
            mood_change_reason = "进行愉快的对话"
        elif any(word in response_lower for word in ["烦", "讨厌", "生气", "不满", "厌倦"]):
            next_speaker.update_mood('negative_conversation', -0.15, f"在{location}进行不愉快的对话")
            mood_change_reason = "进行不愉快的对话"
        elif any(word in response_lower for word in ["有趣", "笑", "幽默", "快乐"]):
            next_speaker.update_mood('humorous_conversation', 0.1, f"在{location}进行幽默的对话")
            mood_change_reason = "进行幽默的对话"
        else:
            # 默认情况，根据MBTI特性更新心情
            if next_speaker.mbti.startswith('E'):  # 外向型从对话中获得能量
                next_speaker.update_mood('conversation', 0.05, f"在{location}参与对话")
                mood_change_reason = "参与社交对话"
            else:  # 内向型社交会略微消耗能量
                next_speaker.update_mood('conversation', -0.02, f"在{location}不得不社交")
                mood_change_reason = "不得不参与社交"
        
        # 其他人也会受到对话的影响
        for agent in participating_agents:
            if agent.id != next_speaker.id and agent.id not in said_goodbye:
                # 根据对话内容和MBTI特性调整其他人的心情
                if mood_change_reason:
                    # 调整幅度比说话者小
                    intensity = 0.05 if "愉快" in mood_change_reason else (
                                -0.05 if "不愉快" in mood_change_reason else 0.02)
                    
                    # 外向型和内向型对社交的反应不同
                    if "社交" in mood_change_reason:
                        intensity = 0.03 if agent.mbti.startswith('E') else -0.01
                        
                    agent.update_mood('passive_conversation', intensity, f"听{next_speaker.name}在{location}说话")
        
        # 更新对话状态
        last_speaker = next_speaker
        dialogue_context += f"\n{next_speaker.name}: {response}"
        
        # 如果超过80%的智能体说了再见，提前结束对话
        if len(said_goodbye) >= len(participating_agents) * 0.8:
            break

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
            # 检查llm_engine是否为字符串，如果是，创建真正的LLM引擎对象
            from llm_engine.factory import LLMEngineFactory
            llm_engine = agent.llm_engine
            if isinstance(llm_engine, str):
                llm_engine = LLMEngineFactory.create_engine(llm_engine)
                
            response = llm_engine.generate(prompt)
            
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

def run_simulation(agents, rounds=10, visual_mode=False, max_conversation_participants=4, environment_init=False, location_count=5):
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
            
            # 并行制定计划
            if len(agents) > 1:
                # 准备所有智能体的计划制定提示
                all_prompts = []
                for agent in agents:
                    # 为每个智能体构建计划提示
                    # 获取最近的记忆，构建上下文
                    recent_short_memories = agent.short_term_memory[-min(10, len(agent.short_term_memory)):]
                    recent_short_memories_text = "\n".join(recent_short_memories)
                    
                    # 提取长期记忆中的关键信息
                    key_long_memories = []
                    for memory in agent.long_term_memory[-20:]:  # 最近20条长期记忆
                        for location in available_locations:
                            if location in memory:
                                key_long_memories.append(memory)
                                break
                    key_long_memories_text = "\n".join(key_long_memories[-5:])  # 最多5条与位置相关的长期记忆
                    
                    # 获取当前所在位置
                    current_location = None
                    for loc_name, loc in world.locations.items():
                        if agent.id in loc.current_agents:
                            current_location = loc_name
                            break
                    if not current_location and available_locations:
                        current_location = random.choice(available_locations)
                        
                    # 构建位置描述文本
                    locations_text = ""
                    for loc in available_locations:
                        desc = location_descriptions.get(loc, "")
                        locations_text += f"- {loc}: {desc}\n"
                        
                    # 构建提示，用于生成计划
                    prompt = f"""作为{agent.name}，一个{agent.background['gender']}性{agent.background['age']}岁{agent.background['occupation']}，MBTI性格类型为{agent.mbti}，我需要根据我的背景和记忆制定今天的活动计划。

我的背景信息:
- 年龄: {agent.background['age']}岁
- 性别: {agent.background['gender']}
- 职业: {agent.background['occupation']}
- 教育水平: {agent.background['education']}
- 家乡: {agent.background['hometown']}
- 外貌: {agent.appearance}

我当前所在位置: {current_location}

可用的位置:
{locations_text}

我的近期记忆:
{recent_short_memories_text}

我的重要长期记忆:
{key_long_memories_text}

请根据以上信息，为我制定一个符合我性格特点和背景的一天计划，包括我要去的地点、在每个地点停留的时间和我要做的事情。

计划格式要求:
1. 分为{rounds_per_day}个时间段（上午、中午、下午、晚上等）
2. 每个时间段指定一个地点（从可用位置中选择）
3. 每个时间段1-2句话描述我计划做的事情
4. 行动计划要符合我的MBTI性格和职业背景
5. 考虑我的近期记忆中的活动和人际互动
6. 如果我最近与某人有互动，可以考虑安排与他们再次见面

请直接输出JSON格式，格式如下:
[
  {{
    "location": "地点名称",
    "duration": 1,
    "activity": "计划做的事情",
    "status": "状态描述（如'工作中'、'放松中'、'用餐中'等）"
  }},
  ...
]

确保输出是有效的JSON格式，并且每个地点都是从可用位置列表中选择的。每个时间段的duration总和应该是{rounds_per_day}。
"""
                    all_prompts.append(prompt)
                
                # 获取第一个智能体的LLM引擎进行批量生成
                llm_engine = agents[0].llm_engine
                
                print(f"正在为 {len(agents)} 个智能体并行制定计划...")
                # 检查llm_engine是否为字符串，如果是，需要创建真正的LLM引擎对象
                from llm_engine.factory import LLMEngineFactory
                if isinstance(llm_engine, str):
                    llm_engine = LLMEngineFactory.create_engine(llm_engine)
                
                # 如果不支持batch_generate，则逐个处理
                if hasattr(llm_engine, 'batch_generate'):
                    plan_responses = llm_engine.batch_generate(all_prompts)
                else:
                    print("LLM引擎不支持批量生成，将逐个处理...")
                    plan_responses = []
                    for prompt in all_prompts:
                        response = llm_engine.generate(prompt)
                        plan_responses.append(response)
                
                # 处理每个智能体的计划
                for i, (agent, response) in enumerate(zip(agents, plan_responses)):
                    print(f"处理 {agent.name} 的计划...")
                    
                    # 解析计划响应并设置到智能体
                    try:
                        # 提取JSON部分（可能有其他文本）
                        json_start = response.find('[')
                        json_end = response.rfind(']') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            plan_json = response[json_start:json_end]
                            agent._set_plan_from_json(plan_json, available_locations, rounds_per_day)
                            
                            # 打印计划摘要
                            if agent.daily_plan:
                                plan_summary = f"{agent.name} 的今日计划："
                                for j, item in enumerate(agent.daily_plan):
                                    plan_summary += f"\n{j+1}. {item['location']}({item['duration']}轮): {item['activity']} ({item['status']})"
                                print(plan_summary)
                        else:
                            print(f"无法从响应中提取JSON计划，将使用常规方法为 {agent.name} 制定计划")
                            agent.plan(
                                available_locations=list(world.locations.keys()),
                                location_descriptions=location_descriptions,
                                max_rounds=rounds_per_day
                            )
                    except Exception as e:
                        print(f"解析 {agent.name} 的计划时出错: {e}，将使用常规方法制定计划")
                        agent.plan(
                            available_locations=list(world.locations.keys()),
                            location_descriptions=location_descriptions,
                            max_rounds=rounds_per_day
                        )
            else:
                # 如果只有一个智能体，使用常规方法
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
                            run_dialogue(participants, location_name, current_round, max_conversation_participants)
                
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
