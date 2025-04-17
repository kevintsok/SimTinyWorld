import os
import time
import argparse
import shutil
from agent.base_agent import BaseAgent
from environment.world import World
from environment.environment_descriptions import EnvironmentDescriptions
import random
import json

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
    
    Args:
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
        
        # 记录初始位置到短期记忆中
        agent.add_memory(f"我现在在{location}。{world.locations[location].description}")
    
    try:
        # 模拟一段时间内的活动
        for _ in range(rounds):
            print("\n=== 新一轮活动开始 ===")
            
            # 让每个智能体随机移动
            for agent in agents:
                current_location = None
                for loc_name, loc in world.locations.items():
                    if agent.id in loc.current_agents:
                        current_location = loc_name
                        break
                
                if current_location:
                    connected_locations = world.get_connected_locations(current_location)
                    if connected_locations:
                        target_location = random.choice(connected_locations)
                        if world.move_agent(agent.id, target_location):
                            print(f"{agent.name}从{current_location}移动到了{target_location}")
                            # 记录移动到短期记忆
                            agent.add_memory(f"我从{current_location}移动到了{target_location}。{world.locations[target_location].description}")
            
            # 打印每个地点的智能体情况
            print("\n=== 当前各地点智能体分布 ===")
            for location_name, location in world.locations.items():
                agents_at_location = world.get_agents_at_location(location_name)
                if agents_at_location:
                    agent_names = [agent.name for agent in agents_at_location]
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
                        
                        # 外向型智能体优先发言
                        participants = sorted(participants, key=lambda a: 0 if a.mbti.startswith('E') else 1)
                        
                        # 初始化对话状态
                        conversation_round = 1
                        conversation_history = []
                        goodbye_flags = {a.id: False for a in participants}  # 记录每个智能体是否已道别
                        
                        # 获取环境描述
                        environment_desc = env_descriptions.get_description(location_name)
                        
                        # 生成可能的对话话题
                        potential_topics = env_descriptions.get_topics(location_name)
                        suggested_topic = random.choice(potential_topics)
                        
                        # 记录当前场景中的其他人
                        for agent in participants:
                            # 获取当前场景中的其他参与者
                            other_participants = [p for p in participants if p.id != agent.id]
                            other_participants_info = []
                            
                            for p in other_participants:
                                other_participants_info.append(f"{p.name}({p.mbti}，{p.background['gender']}性{p.background['occupation']}，外貌：{p.appearance})")
                                
                            # 记录到记忆中
                            agent.add_memory(f"我在{location_name}遇到了: {', '.join(other_participants_info)}")
                        
                        # 第一轮对话：第一个智能体发言，其他人回应
                        # 获取第一个发言者（通常是外向型）
                        first_speaker = participants[0]
                        
                        # 构建智能体信息，用于对话提示
                        participants_info = []
                        for agent in participants:
                            if agent.id != first_speaker.id:  # 排除发言者自己
                                participants_info.append({
                                    "name": agent.name,
                                    "mbti": agent.mbti,
                                    "gender": agent.background['gender'],
                                    "occupation": agent.background['occupation'],
                                    "appearance": agent.appearance
                                })
                        
                        # 构建第一个发言者的提示
                        other_participants_text = ""
                        for idx, p in enumerate(participants_info):
                            other_participants_text += f"参与者{idx+1}: {p['name']}，{p['gender']}性{p['occupation']}，{p['mbti']}类型，外貌：{p['appearance']}\n"
                        
                        # 第一个智能体发起对话
                        query1 = f"""
你是{first_speaker.name}，一个{first_speaker.background['gender']}性{first_speaker.background['occupation']}，性格是{first_speaker.mbti}，{first_speaker.background['age']}岁，来自{first_speaker.background['hometown']}。
你的外貌: {first_speaker.appearance}

你现在在{location_name}，正在一个{len(participants)}人的小组讨论中。其他参与者包括：
{other_participants_text}

当前环境描述:
{environment_desc}

请根据以下提示生成一句对话开场白:
1. 考虑周围环境的特点和氛围
2. 根据你的MBTI性格({first_speaker.mbti})，表现出对环境和对方的自然反应
3. 这是一个多人讨论，你的开场白应该面向所有人，或者可以指名其中一人
4. 可以围绕"{suggested_topic}"这个话题展开对话

要求:
- 自然、有深度的开场白，避免简单问候
- 不要简单自我介绍
- 表现出你的性格特点和对当前环境的感知
- 字数在20-50字之间
"""
                        
                        # 获取第一个智能体的回应
                        response = first_speaker.query_memory(query1)
                        print(f"{first_speaker.name}: {response}")
                        conversation_history.append(f"{first_speaker.name}: {response}")
                        
                        # 添加对话到可视化器
                        world.add_agent_dialog(first_speaker.name, response)
                        
                        # 记录到发言者的记忆中（只保存在短期记忆中）
                        first_speaker.add_memory(f"在{location_name}对话中我说：{response}")
                        
                        # 定义用于检查道别的关键词
                        goodbye_words = ["再见", "拜拜", "下次见", "告辞", "走了", "bye", "告别", "回头见", "待会见", "告退", "失陪"]
                        
                        # 进行多轮对话，每轮让一个智能体发言
                        max_rounds = 3 + len(participants)  # 让每个人至少有机会说一句话
                        current_round = 1
                        
                        while current_round < max_rounds and sum(goodbye_flags.values()) < len(participants) // 2:
                            if visual_mode:
                                time.sleep(0.5)  # 暂停使对话看起来更自然
                            
                            # 按顺序让每个智能体发言（跳过已经告别的智能体）
                            for speaker_idx in range(len(participants)):
                                speaker = participants[speaker_idx]
                                
                                # 如果当前智能体已经道别，跳过
                                if goodbye_flags[speaker.id]:
                                    continue
                                
                                # 获取上一个发言者
                                last_speaker_name = conversation_history[-1].split(": ")[0]
                                last_speech = conversation_history[-1].split(": ")[1]
                                
                                # 如果是第一个智能体且已经发过言，跳过
                                if speaker.id == first_speaker.id and current_round == 1:
                                    continue
                                
                                # 构建当前智能体的对话提示
                                history_text = "\n".join(conversation_history[-min(len(conversation_history), 5):])
                                
                                # 根据对话进程决定是否应该结束对话
                                should_consider_ending = current_round > 2
                                ending_probability = 0.3 if should_consider_ending else 0.0
                                
                                # 构建当前发言者的提示
                                other_participants_text = ""
                                for idx, other_agent in enumerate(participants):
                                    if other_agent.id != speaker.id:  # 排除发言者自己
                                        other_participants_text += f"参与者{idx+1}: {other_agent.name}，{other_agent.background['gender']}性{other_agent.background['occupation']}，{other_agent.mbti}类型，外貌：{other_agent.appearance}\n"
                                
                                query = f"""
你是{speaker.name}，一个{speaker.background['gender']}性{speaker.background['occupation']}，性格是{speaker.mbti}，{speaker.background['age']}岁，来自{speaker.background['hometown']}。
你的外貌: {speaker.appearance}

你现在在{location_name}，参与一个{len(participants)}人的对话，环境是：{environment_desc}
其他参与者包括：
{other_participants_text}

对话历史：
{history_text}

刚才{last_speaker_name}说: "{last_speech}"

请根据以下提示生成回应:
1. 表现出你的{speaker.mbti}性格特点
2. 回应内容要与上下文相关，可以针对最近的发言，也可以提出新的观点
3. 你可以回应特定的某个人，也可以面向所有人
4. 可以围绕"{suggested_topic}"这个话题
5. 当前是第{current_round}轮对话，{"如果觉得合适，可以考虑结束对话" if should_consider_ending else "请保持对话流畅"}

要求:
- 回答要真实自然，像是在真实多人对话中的一句话
- 体现你的性格特点
- 字数在20-50字之间
- 如果你觉得对话该结束了，可以自然地道别
"""
                                
                                # 获取当前智能体的回应
                                response = speaker.query_memory(query)
                                print(f"{speaker.name}: {response}")
                                conversation_history.append(f"{speaker.name}: {response}")
                                
                                # 添加对话到可视化器
                                world.add_agent_dialog(speaker.name, response)
                                
                                # 记录到智能体的记忆中（只保存在短期记忆中）
                                speaker.add_memory(f"在{location_name}对话中，{last_speaker_name}说：{last_speech}，我回应：{response}")
                                
                                # 检查是否有道别的意图
                                for word in goodbye_words:
                                    if word in response:
                                        goodbye_flags[speaker.id] = True
                                        break
                                
                                # 如果已经有足够多的人说再见了，结束对话
                                if sum(goodbye_flags.values()) >= len(participants) // 2:
                                    break
                                
                                # 更新世界可视化，仅在可视化模式下
                                if visual_mode:
                                    for _ in range(2):
                                        world.update_world()
                                        time.sleep(0.1)
                                        
                            # 如果已经有足够多的人说再见了，让剩余的人也说再见
                            if sum(goodbye_flags.values()) >= len(participants) // 2 and sum(goodbye_flags.values()) < len(participants):
                                # 让所有未道别的智能体道别
                                for agent in participants:
                                    if not goodbye_flags[agent.id]:
                                        goodbye_msg = random.choice([
                                            "我也该走了，下次再聊！",
                                            "时间不早了，我也先告辞了。",
                                            "既然大家都要走了，那我们改天再聊吧！",
                                            "看来讨论要结束了，很高兴和大家交流！"
                                        ])
                                        print(f"{agent.name}: {goodbye_msg}")
                                        conversation_history.append(f"{agent.name}: {goodbye_msg}")
                                        world.add_agent_dialog(agent.name, goodbye_msg)
                                        agent.add_memory(f"在{location_name}对话即将结束时，我说：{goodbye_msg}")
                                
                                        # 更新世界可视化，仅在可视化模式下
                                        if visual_mode:
                                            world.update_world()
                                            time.sleep(0.1)
                            
                            # 增加轮次计数
                            current_round += 1
                        
                        # 记录完整对话到所有参与者的记忆中（只保存在短期记忆中）
                        full_conversation = "\n".join(conversation_history)
                        participant_names = [agent.name for agent in participants]
                        
                        for agent in participants:
                            agent.add_memory(f"在{location_name}与{', '.join([name for name in participant_names if name != agent.name])}的完整对话记录：\n{full_conversation}")
                            # 保存智能体的身份信息
                            agent.save_identity()
            
            # 更新世界可视化，仅在可视化模式下
            if visual_mode:
                for _ in range(10):  # 更新多次以确保动画流畅
                    world.update_world()
                    time.sleep(0.1)
            
            time.sleep(1)  # 暂停一下，让输出更容易阅读
        
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
    
    args = parser.parse_args()
    
    # 处理模式设置 - 如果使用了--continue/-c参数，将mode设为"continue"
    if args.continue_mode:
        args.mode = "continue"
    
    print(f"以 {args.mode} 模式启动模拟...")
    print(f"使用{'可视化' if args.visual else '终端'}模式")
    print(f"智能体数量: {args.agents}")
    print(f"地点数量: {args.locations}")
    print(f"对话最大参与者数量: {args.max_participants}")
    
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