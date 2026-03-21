import random
import time
from typing import List, Dict, Any

def check_conversation_end(participants, conversation_history, location_name, llm_engine):
    """
    使用LLM判断当前对话是否已经可以结束
    
    Args:
        participants: 参与对话的智能体列表
        conversation_history: 当前的对话历史
        location_name: 对话发生的位置
        llm_engine: LLM引擎实例，用于分析对话
        
    Returns:
        is_ending: 是否应当结束对话
        goodbye_agents: 应该离开的智能体ID列表
    """
    # 获取最近的对话内容（最多10轮）
    recent_history = conversation_history[-min(10, len(conversation_history)):]
    recent_history_text = "\n".join(recent_history)
    
    # 提取参与者名字
    participant_names = [agent.name for agent in participants]
    
    # 构建提示
    prompt = f"""作为对话分析师，请分析以下在{location_name}进行的对话，判断对话是否已经自然结束或应该结束。

对话参与者: {', '.join(participant_names)}
最近的对话内容:
{recent_history_text}

请分析以下几点:
1. 对话是否已经进入结束阶段（例如有人道别、约定下次见面等）
2. 话题是否已经自然结束，没有新的话题被引入
3. 是否所有人都直接或间接表达了结束对话的意愿
4. 对话是否陷入尴尬或重复

请给出分析结果:
- 对话是否应该结束（是/否）
- 哪些参与者已明确或暗示想要结束对话

回答格式：
对话结束: 是/否
准备离开的参与者: [参与者名字列表，如没有，则留空]
"""
    
    # 使用第一个智能体的LLM引擎进行分析
    response = llm_engine.generate(prompt)
    
    # 解析回应
    should_end = False
    goodbye_agents = []
    
    # 尝试从回应中提取信息
    try:
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("对话结束:") or line.startswith("对话结束："):
                value = line.split(':', 1)[1].strip() if ':' in line else line.split('：', 1)[1].strip()
                should_end = value == "是"
            
            if line.startswith("准备离开的参与者:") or line.startswith("准备离开的参与者："):
                value = line.split(':', 1)[1].strip() if ':' in line else line.split('：', 1)[1].strip()
                if value and value != "[]" and value.lower() != "无":
                    # 移除可能的方括号并分割名称
                    value = value.replace('[', '').replace(']', '')
                    names = [name.strip() for name in value.split(',')]
                    
                    # 找到对应的智能体ID
                    for name in names:
                        for agent in participants:
                            if agent.name == name or name in agent.name:
                                goodbye_agents.append(agent.id)
    except Exception as e:
        print(f"解析LLM回应时出错: {e}")
    
    return should_end, goodbye_agents

def initiate_conversation(participants, location_name, environment_desc, world, suggested_topic=None):
    """
    初始化并进行一组智能体之间的对话
    
    Args:
        participants: 参与对话的智能体列表
        location_name: 对话发生的位置名称
        environment_desc: 环境描述
        world: 世界实例，用于可视化对话
        suggested_topic: 建议的对话话题，如果为None则不指定
        
    Returns:
        conversation_history: 完整的对话历史记录
    """
    # 排序参与者，外向型优先发言
    participants = sorted(participants, key=lambda a: 0 if a.mbti.startswith('E') else 1)
    
    # 初始化对话状态
    conversation_history = []
    goodbye_flags = {a.id: False for a in participants}  # 记录每个智能体是否已道别
    first_member = participants[0]  # 第一个发言的人
    
    # 获取LLM引擎实例（从第一个智能体获取）
    llm_engine = first_member.llm_engine

    # 如果没有指定话题，生成随机话题
    if not suggested_topic:
        potential_topics = [
            "最近的天气", "周围的环境", "当前的心情", "最近的工作", 
            "兴趣爱好", "未来计划", "生活变化", "最近的见闻",
            "特别的经历", "感兴趣的书籍或电影", "最近的新闻"
        ]
        suggested_topic = random.choice(potential_topics)
    
    # 记录当前场景中的其他人
    for agent in participants:
        # 获取当前场景中的其他参与者
        other_participants = [p for p in participants if p.id != agent.id]
        other_participants_info = []
        
        for p in other_participants:
            other_participants_info.append(f"{p.name}({p.background['gender']}性，外貌：{p.appearance})")
            
        # 记录到记忆中
        agent.add_memory(f"我在{location_name}遇到了: {', '.join(other_participants_info)}")
    
    # 构建智能体信息，用于对话提示
    participants_info = []
    for agent in participants:
        if agent.id != first_member.id:  # 排除发言者自己
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
        other_participants_text += f"参与者{idx+1}: {p['name']}，{p['gender']}性，外貌：{p['appearance']}\n"
    
    # 第一个智能体发起对话
    query1 = f"""
你是{first_member.name}，一个{first_member.background['gender']}性{first_member.background['occupation']}，性格是{first_member.mbti}，{first_member.background['age']}岁，来自{first_member.background['hometown']}。
你的外貌: {first_member.appearance}

你现在在{location_name}，正在一个{len(participants)}人的小组讨论中。其他参与者包括：
{other_participants_text}

当前环境描述:
{environment_desc}

请根据以下提示生成一句对话开场白:
1. 考虑周围环境的特点和氛围
2. 根据你的MBTI性格({first_member.mbti})，表现出对环境和对方的自然反应
3. 这是一个多人讨论，你的开场白应该面向所有人，或者可以指名其中一人
4. 可以围绕"{suggested_topic}"这个话题展开对话

要求:
- 自然、有深度的开场白，避免简单问候
- 不要简单自我介绍
- 表现出你的性格特点和对当前环境的感知
- 字数在20-50字之间
"""
    
    # 获取第一个智能体的回应
    response = first_member.query_memory(query1)
    print(f"{first_member.name}: {response}")
    conversation_history.append(f"{first_member.name}: {response}")
    
    # 添加对话到可视化器
    world.add_agent_dialog(first_member.name, response)
    
    # 记录到发言者的记忆中（只保存在短期记忆中）
    first_member.add_memory(f"在{location_name}对话中我说：{response}")
    
    # 定义用于检查道别的关键词
    goodbye_words = ["再见", "拜拜", "下次见", "告辞", "走了", "bye", "告别", "回头见", "待会见", "告退", "失陪"]
    
    # 持续对话，直到半数以上的智能体选择道别
    current_round = 1
    visual_mode = world.visual_mode

    while sum(goodbye_flags.values()) < len(participants) // 2:
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
            if speaker.id == first_member.id and current_round == 1:
                continue
            
            # 构建当前智能体的对话提示
            history_text = "\n".join(conversation_history[-min(len(conversation_history), 5):])
            
            # 根据对话进程决定是否应该结束对话
            should_consider_ending = current_round > 5  # 对话进行5轮后可考虑结束
            
            # 构建当前发言者的提示
            other_participants_text = ""
            for idx, other_agent in enumerate(participants):
                if other_agent.id != speaker.id:  # 排除发言者自己
                    other_participants_text += f"参与者{idx+1}: {other_agent.name}，{other_agent.background['gender']}性，外貌：{other_agent.appearance}\n"
            
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
        
        # 使用LLM判断对话是否应该结束
        if current_round >= 3:  # 至少进行3轮对话后再判断
            should_end, goodbye_agent_ids = check_conversation_end(
                participants=participants,
                conversation_history=conversation_history,
                location_name=location_name,
                llm_engine=llm_engine
            )
            
            # 更新已道别的智能体标记
            for agent_id in goodbye_agent_ids:
                goodbye_flags[agent_id] = True
                
            # 如果LLM认为对话应该结束，并且至少有一人准备离开
            if should_end and (len(goodbye_agent_ids) > 0 or sum(goodbye_flags.values()) > 0):
                print("LLM分析认为对话已经可以自然结束")
                break
                
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
        
    return conversation_history 