import os
import time
import random
import json
import threading
from agent.base_agent import BaseAgent
from environment.world import World
from environment.environment_descriptions import EnvironmentDescriptions
from agent.interact import initiate_conversation
from utils.logger import SimulationLogger

# 创建全局锁，用于保护对智能体状态的修改
agent_locks = {}
global_lock = threading.Lock()

def run_dialogue(agents, location, round_index, max_participants=4, logger=None):
    """运行一轮对话，让智能体之间交互
    
    Args:
        agents: 参与对话的智能体列表
        location: 对话发生的位置
        round_index: 当前轮次索引
        max_participants: 最大参与者数量，默认为4
        logger: 日志记录器
    """
    # 为避免多线程访问冲突，对参与对话的智能体列表进行复制
    participating_agents = agents.copy()
    
    # 如果智能体数量大于max_participants，随机选择max_participants个
    if len(participating_agents) > max_participants:
        participating_agents = random.sample(participating_agents, max_participants)
    
    # 确保每个智能体都有锁
    for agent in participating_agents:
        with global_lock:
            if agent.id not in agent_locks:
                agent_locks[agent.id] = threading.Lock()
    
    # 如果只有一个智能体，不进行对话
    if len(participating_agents) < 2:
        solo_agent = participating_agents[0]
        solo_thought = f"我在{location}，周围没有其他人，感到{solo_agent.mood['description']}。"
        
        # 使用智能体专用锁保护内存修改
        with agent_locks[solo_agent.id]:
            solo_agent.add_memory(solo_thought)
        
        # 记录独处行为
        if logger:
            logger.log_agent_action(solo_agent, "独自一人", location)
            logger.log_agent_memory(solo_agent, solo_thought)
            
        # 更新独自一人时的心情
        if random.random() < 0.7:  # 70%的概率更新心情
            with agent_locks[solo_agent.id]:
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
    
    # 记录完整对话内容，用于日志
    full_dialogue = f"位置: {location}\n"
    
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
            # 使用智能体专用锁保护对话生成
            with agent_locks[next_speaker.id]:
                response = next_speaker.respone(query_for_agent)
        except Exception as e:
            error_msg = f"获取{next_speaker.name}的回复时出错: {e}"
            print(error_msg)
            if logger:
                logger.log_error(error_msg, next_speaker)
            response = f"（看起来有些犹豫，没有说话）"
        
        # 打印对话内容
        print(f"{next_speaker.name} ({next_speaker.status}, {next_speaker.mood['description']}): {response}")
        
        # 添加到完整对话记录
        full_dialogue += f"{next_speaker.name} ({next_speaker.status}, {next_speaker.mood['description']}): {response}\n"
        
        # 更新对话记忆
        memory_text = f"在{location}，我对大家说：'{response}'"
        with agent_locks[next_speaker.id]:
            next_speaker.add_memory(memory_text)
        
        # 记录对话记忆
        if logger:
            logger.log_agent_memory(next_speaker, memory_text)
        
        # 为其他参与者添加听到的对话记忆
        for agent in participating_agents:
            if agent.id != next_speaker.id:
                agent_memory = f'在{location}，{next_speaker.name}说："{response}"'
                with agent_locks[agent.id]:
                    agent.add_memory(agent_memory)
                
                # 记录对话记忆
                if logger:
                    logger.log_agent_memory(agent, agent_memory)
        
        # 更新发言者的心情
        # 对话后根据内容和性格更新心情
        response_lower = response.lower()
        # 检测对话情绪
        mood_change_reason = ""
        if "再见" in response_lower or "拜拜" in response_lower or "走了" in response_lower:
            said_goodbye.add(next_speaker.id)
            mood_change_reason = f"要离开{location}的对话"
        elif any(word in response_lower for word in ["高兴", "开心", "愉快", "喜欢", "好玩"]):
            with agent_locks[next_speaker.id]:
                next_speaker.update_mood('positive_conversation', 0.15, f"在{location}进行愉快的对话")
            mood_change_reason = "进行愉快的对话"
        elif any(word in response_lower for word in ["烦", "讨厌", "生气", "不满", "厌倦"]):
            with agent_locks[next_speaker.id]:
                next_speaker.update_mood('negative_conversation', -0.15, f"在{location}进行不愉快的对话")
            mood_change_reason = "进行不愉快的对话"
        elif any(word in response_lower for word in ["有趣", "笑", "幽默", "快乐"]):
            with agent_locks[next_speaker.id]:
                next_speaker.update_mood('humorous_conversation', 0.1, f"在{location}进行幽默的对话")
            mood_change_reason = "进行幽默的对话"
        else:
            # 默认情况，根据MBTI特性更新心情
            with agent_locks[next_speaker.id]:
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
                    
                    with agent_locks[agent.id]:
                        agent.update_mood('passive_conversation', intensity, f"听{next_speaker.name}在{location}说话")
        
        # 更新对话状态
        last_speaker = next_speaker
        dialogue_context += f"\n{next_speaker.name}: {response}"
        
        # 如果超过80%的智能体说了再见，提前结束对话
        if len(said_goodbye) >= len(participating_agents) * 0.8:
            break

    # 记录完整对话
    if logger:
        logger.log_dialogue(location, participating_agents, full_dialogue)

def update_agents_wealth(agents, world, logger=None):
    """
    根据智能体的活动和交互情况，判断并更新其财富值
    
    参数:
    agents: 所有智能体列表
    world: 世界实例
    logger: 日志记录器
    """
    print("\n=== 更新智能体财富值 ===")
    if logger:
        logger.log_simulation("=== 更新智能体财富值 ===")
    
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
- 时间财富: {agent.wealth["time"]:.2f} (-1.0表示极度忙碌，1.0表示极度空闲)
- 社交财富: {agent.wealth["social"]:.2f} (-1.0表示极度孤独，1.0表示极度活跃)
- 健康财富: {agent.wealth["health"]:.2f} (-1.0表示极度不健康，1.0表示极度健康)
- 精神财富: {agent.wealth["mental"]:.2f} (-1.0表示极度压力，1.0表示极度放松)
- 金钱财富: {agent.wealth["money"]:.2f}元 

最近活动:
{recent_activities}

请根据活动内容，评估是否需要调整财富值。返回格式为JSON，包含以下字段：
1. time_change: 时间财富变化，范围-0.2到0.2
2. social_change: 社交财富变化，范围-0.2到0.2
3. health_change: 健康财富变化，范围-0.2到0.2
4. mental_change: 精神财富变化，范围-0.2到0.2
5. money_change: 金钱变化，范围-1000到1000
6. reason: 变化原因的简短描述

示例返回:
{{
  "time_change": -0.1,
  "social_change": 0.15,
  "health_change": 0.0,
  "mental_change": 0.05,
  "money_change": -50,
  "reason": "参加社交活动消耗了时间，但提升了社交能力和心情，花费了一些金钱"
}}

只考虑合理和相关的变化，不必强制所有财富都变化。如果某方面没有明显变化，对应值应为0。
"""
        
        # 调用LLM获取财富变化评估
        try:
            wealth_analysis = agent._generate_with_llm(prompt)
            
            # 解析返回的JSON
            try:
                # 找到JSON开始和结束位置
                json_start = wealth_analysis.find('{')
                json_end = wealth_analysis.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    wealth_json = wealth_analysis[json_start:json_end]
                    wealth_changes = json.loads(wealth_json)
                    
                    # 更新财富值
                    old_wealth = {k: v for k, v in agent.wealth.items()}  # 保存旧值用于记录
                    
                    if "time_change" in wealth_changes:
                        agent.wealth["time"] = max(-1.0, min(1.0, agent.wealth["time"] + wealth_changes["time_change"]))
                    if "social_change" in wealth_changes:
                        agent.wealth["social"] = max(-1.0, min(1.0, agent.wealth["social"] + wealth_changes["social_change"]))
                    if "health_change" in wealth_changes:
                        agent.wealth["health"] = max(-1.0, min(1.0, agent.wealth["health"] + wealth_changes["health_change"]))
                    if "mental_change" in wealth_changes:
                        agent.wealth["mental"] = max(-1.0, min(1.0, agent.wealth["mental"] + wealth_changes["mental_change"]))
                    if "money_change" in wealth_changes:
                        agent.wealth["money"] = max(0, agent.wealth["money"] + wealth_changes["money_change"])
                    
                    # 生成财富变化描述
                    reason = wealth_changes.get("reason", "根据最近活动调整")
                    
                    # 记录财富变化
                    wealth_change_desc = f"{agent.name}财富更新: 时间[{old_wealth['time']:.2f} -> {agent.wealth['time']:.2f}], "
                    wealth_change_desc += f"社交[{old_wealth['social']:.2f} -> {agent.wealth['social']:.2f}], "
                    wealth_change_desc += f"健康[{old_wealth['health']:.2f} -> {agent.wealth['health']:.2f}], "
                    wealth_change_desc += f"精神[{old_wealth['mental']:.2f} -> {agent.wealth['mental']:.2f}], "
                    wealth_change_desc += f"金钱[{old_wealth['money']:.2f} -> {agent.wealth['money']:.2f}]"
                    wealth_change_desc += f" - 原因: {reason}"
                    
                    print(wealth_change_desc)
                    if logger:
                        logger.log_simulation(wealth_change_desc)
                    
                    # 添加财富变化到智能体记忆
                    if any(abs(old_wealth[k] - agent.wealth[k]) > 0.05 for k in ["time", "social", "health", "mental"]) or abs(old_wealth["money"] - agent.wealth["money"]) > 10:
                        memory_text = f"我感觉到了一些变化。{reason}"
                        agent.add_memory(memory_text)
                        if logger:
                            logger.log_agent_memory(agent, memory_text)
            except Exception as e:
                error_msg = f"解析{agent.name}的财富变化时出错: {e}"
                print(error_msg)
                if logger:
                    logger.log_error(error_msg, agent)
        except Exception as e:
            error_msg = f"计算{agent.name}的财富变化时出错: {e}"
            print(error_msg)
            if logger:
                logger.log_error(error_msg, agent)

def run_dialogue_thread(agents, location, round_index, max_participants, logger):
    """在单独线程中运行对话的包装函数
    
    Args:
        agents: 参与对话的智能体列表
        location: 对话发生的位置
        round_index: 当前轮次索引
        max_participants: 最大参与者数量
        logger: 日志记录器
    """
    try:
        if agents:
            print(f"\n在 {location} 的智能体: {', '.join([a.name for a in agents])}")
            if logger:
                logger.log_simulation(f"在 {location} 的智能体: {', '.join([a.name for a in agents])}")
            
            # 运行对话
            if len(agents) > 0:
                run_dialogue(agents, location, round_index, max_participants, logger)
        else:
            print(f"\n{location}没有智能体")
            if logger:
                logger.log_simulation(f"{location}没有智能体")
    except Exception as e:
        error_msg = f"在{location}运行对话时出错: {e}"
        print(error_msg)
        if logger:
            logger.log_error(error_msg)

def run_simulation(agents, rounds=10, visual_mode=False, max_conversation_participants=4, environment_init=False, location_count=5):
    """运行模拟
    
    Args:
        agents: 智能体列表
        rounds: 每天模拟的轮数
        visual_mode: 是否使用可视化模式
        max_conversation_participants: 每次对话的最大参与者数量
        environment_init: 是否初始化环境描述
        location_count: 位置数量
    """
    # 创建日志记录器
    logger = SimulationLogger()
    
    # 记录模拟参数
    logger.log_simulation(f"模拟参数: 智能体数量={len(agents)}, 每天轮数={rounds}, 位置数量={location_count}")
    
    # 创建环境描述
    descriptions = EnvironmentDescriptions()
    descriptions.initialize_environment(force=environment_init)
    
    # 创建世界实例（如果不存在）
    world = World.get_instance()
    if world is None:
        world = World(visual_mode=visual_mode, location_count=location_count)
    
    # 使用前location_count个默认位置进行初始化
    world.init_locations(descriptions.default_locations[:location_count])
    
    # 为每个智能体分配初始位置
    for agent in agents:
        random_location = random.choice(list(world.locations.keys()))
        world.add_agent_to_location(agent, random_location)
        agent.add_memory(f"我现在在{random_location}。")
        
        # 记录智能体初始位置
        if logger:
            logger.log_agent_action(agent, "被放置在", random_location)
            logger.log_simulation(f"{agent.name}（{agent.mbti}，{agent.gender}）被放置在{random_location}")
            logger.log_simulation(f"外貌: {agent.appearance}")
            logger.log_simulation(f"财富状态: 时间:{agent.wealth['time']:.2f}, 社交:{agent.wealth['social']:.2f}, 健康:{agent.wealth['health']:.2f}, 精神:{agent.wealth['mental']:.2f}, 金钱:{agent.wealth['money']:.2f}元")
    
    # 开始模拟多天的活动
    days = 3
    for day in range(1, days + 1):
        logger.log_simulation(f"=== 第{day}天开始 ===")
        print(f"\n=== 第{day}天开始 ===")
        
        # 让所有智能体制定计划
        print(f"\n=== 智能体制定计划 ===")
        logger.log_simulation(f"=== 智能体制定计划 ===")
        
        available_locations = list(world.locations.keys())
        location_descriptions = {loc: descriptions.get_location_desc(loc) for loc in available_locations}
        
        for agent in agents:
            try:
                agent.plan(available_locations, location_descriptions, rounds)
                
                # 记录计划
                plan_str = "\n".join([f"{i+1}. 在{item['location']}停留{item['duration']}轮，{item['activity']}" 
                                    for i, item in enumerate(agent.daily_plan)])
                logger.log_simulation(f"{agent.name}的计划:\n{plan_str}")
            except Exception as e:
                error_msg = f"{agent.name}制定计划时出错: {e}"
                print(error_msg)
                logger.log_error(error_msg, agent)
        
        # 模拟每天的多轮活动
        for round_index in range(1, rounds + 1):
            print(f"\n=== 第{day}天 第{round_index}轮活动开始（总第{round_index + (day-1)*rounds}轮）===")
            logger.log_round(day, round_index, rounds)
            
            # 根据计划移动智能体
            for agent in agents:
                try:
                    # 获取计划中的下一个位置
                    next_location = agent.get_next_planned_location()
                    if next_location:
                        # 获取当前位置
                        current_location = None
                        for loc_name, loc in world.locations.items():
                            if agent.id in loc.current_agents:
                                current_location = loc_name
                                break
                        
                        # 如果计划的下一个位置与当前位置不同，移动智能体
                        if current_location and next_location != current_location:
                            world.move_agent(agent, current_location, next_location)
                            memory = f"我从{current_location}移动到了{next_location}。"
                            agent.add_memory(memory)
                            logger.log_agent_move(agent, current_location, next_location)
                            logger.log_agent_memory(agent, memory)
                            print(f"{agent.name} 从 {current_location} 移动到 {next_location}")
                except Exception as e:
                    error_msg = f"{agent.name}移动时出错: {e}"
                    print(error_msg)
                    logger.log_error(error_msg, agent)
            
            # 确认所有位置的智能体分布
            location_agents = {}
            for loc_name, loc in world.locations.items():
                location_agents[loc_name] = []
                for agent_id in loc.current_agents:
                    for agent in agents:
                        if agent.id == agent_id:
                            location_agents[loc_name].append(agent)
                            break
            
            # 在每个位置并行运行对话
            dialogue_threads = []
            for loc_name, loc_agents in location_agents.items():
                # 为每个有智能体的位置创建一个线程
                thread = threading.Thread(
                    target=run_dialogue_thread,
                    args=(loc_agents, loc_name, round_index, max_conversation_participants, logger)
                )
                dialogue_threads.append(thread)
                thread.start()
            
            # 等待所有对话线程完成
            for thread in dialogue_threads:
                thread.join()
            
            print("\n所有地点的对话已完成")
            logger.log_simulation("所有地点的对话已完成")
            
            # 更新智能体计划进度
            for agent in agents:
                agent.update_plan_progress()
        
        # 更新智能体财富值
        update_agents_wealth(agents, world, logger)
        
        # 让智能体休息和反思
        agents_day_summary = []
        for agent in agents:
            # 记录睡眠前状态
            pre_sleep_status = f"{agent.name}: 心情={agent.mood['description']} ({agent.mood['value']:.2f}), 健康={agent.wealth['health']:.2f}, 精神={agent.wealth['mental']:.2f}"
            logger.log_simulation(f"睡眠前: {pre_sleep_status}")
            
            # 睡眠恢复
            try:
                sleep_result = agent.sleep()
                
                # 如果返回的是带有睡眠质量的结果
                if isinstance(sleep_result, dict) and 'score' in sleep_result:
                    logger.log_sleep(agent, sleep_result)
                else:
                    print(f"{agent.name} 睡眠: {sleep_result}")
                    logger.log_simulation(f"{agent.name} 睡眠: {sleep_result}")
            except Exception as e:
                error_msg = f"{agent.name}睡眠时出错: {e}"
                print(error_msg)
                logger.log_error(error_msg, agent)
            
            # 记录睡眠后状态
            post_sleep_status = f"{agent.name}: 心情={agent.mood['description']} ({agent.mood['value']:.2f}), 健康={agent.wealth['health']:.2f}, 精神={agent.wealth['mental']:.2f}"
            agents_day_summary.append(post_sleep_status)
            logger.log_simulation(f"睡眠后: {post_sleep_status}")
        
        # 记录每天总结
        logger.log_day_summary(day, agents_day_summary)
    
    # 关闭日志记录器
    logger.close()
    
    print("\n=== 模拟结束 ===")
    print(f"日志已保存至: {logger.log_dir}")
    return agents
