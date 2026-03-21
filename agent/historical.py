"""
Historical Agent Generator - 使用LLM生成历史人物或国家作为Agent

用法:
    from agent.historical import create_historical_agent, create_country_agent

    # 创建历史人物
    qin = create_historical_agent("秦始皇")
    print(qin.name, qin.mbti, qin.background)

    # 创建国家/组织
    china = create_country_agent("中华人民共和国")
    print(china.name, china.mbti, china.background)
"""

import json
import random
import uuid
from typing import Optional, Dict, Any
from agent.base_agent import BaseAgent
from llm_engine.factory import get_global_engine


def create_historical_agent(
    name: str,
    era: str = None,
    description: str = None,
    config: Dict[str, Any] = None
) -> BaseAgent:
    """
    使用LLM生成历史人物Agent

    Args:
        name: 历史人物名称，如"秦始皇"、"孔子"、"拿破仑"
        era: 时代背景（可选），如"战国时期"、"春秋时代"
        description: 额外描述（可选）
        config: 配置字典（可选）

    Returns:
        BaseAgent: 生成的Agent实例
    """
    engine = get_global_engine()

    # 构建提示词
    prompt = _build_historical_person_prompt(name, era, description)

    # 调用LLM生成
    if engine.mock_mode:
        response = _generate_mock_historical_agent(name, era)
    else:
        response = engine.generate(prompt)

    # 解析响应
    agent_data = _parse_historical_agent_response(response, name, era)

    # 创建Agent
    agent = _create_agent_from_data(agent_data, config)
    return agent


def create_country_agent(
    name: str,
    country_type: str = "nation",
    description: str = None,
    config: Dict[str, Any] = None
) -> BaseAgent:
    """
    使用LLM生成国家/组织Agent

    Args:
        name: 国家/组织名称，如"中华人民共和国"、"美国"、"联合国"
        country_type: 类型，"nation"或"organization"
        description: 额外描述（可选）
        config: 配置字典（可选）

    Returns:
        BaseAgent: 生成的Agent实例
    """
    engine = get_global_engine()

    # 构建提示词
    prompt = _build_country_prompt(name, country_type, description)

    # 调用LLM生成
    if engine.mock_mode:
        response = _generate_mock_country(name, country_type)
    else:
        response = engine.generate(prompt)

    # 解析响应
    agent_data = _parse_country_agent_response(response, name, country_type)

    # 创建Agent
    agent = _create_agent_from_data(agent_data, config)
    return agent


def _build_historical_person_prompt(name: str, era: str, description: str) -> str:
    """构建历史人物生成提示词"""
    era_hint = f"，时代：{era}" if era else ""
    desc_hint = f"，背景：{description}" if description else ""

    return f"""请为"{name}"{era_hint}{desc_hint}生成一个完整的AI智能体档案。

请生成以下JSON格式的信息（只返回JSON，不要有其他内容）：

{{
    "name": "{name}",
    "gender": "男"或"女",
    "age": 生理年龄数字,
    "mbti": "16种MBTI之一",
    "background": {{
        "gender": "男"或"女",
        "age": 生理年龄数字,
        "occupation": "主要身份/职业",
        "education": "教育程度",
        "hometown": "出生地/来源地",
        "description": "200字左右的背景描述，包括时代背景、重要经历、性格形成原因等"
    }},
    "appearance": "150字左右的外貌描述，符合时代和身份特征",
    "personality_traits": ["3-5个性格关键词"],
    "core_values": ["3-5个核心价值观"],
    "famous_quotes": ["2-3句名言或口头禅"],
    "key_memories": [
        "3-5条重要记忆，每条50字左右，要体现时代背景和个人特色"
    ]
}}

要求：
1. MBTI性格要符合历史人物已知的行为模式和性格特点
2. 外貌描述要符合时代特征（如古代人要描述服饰发型）
3. 背景描述要体现历史背景和人物特色
4. 关键记忆要选取该人物最著名的事件
5. 只返回JSON格式，不要有任何前缀或解释文字"""


def _build_country_prompt(name: str, country_type: str, description: str) -> str:
    """构建国家/组织生成提示词"""
    country_type_str = "国家" if country_type == "nation" else "国际组织"
    desc_hint = f"，背景：{description}" if description else ""

    return f"""请为"{name}"（{country_type_str}）生成一个完整的AI智能体档案。

把这个{country_type_str}视为一个独立的"角色"，具有自己的"性格"和"行为模式"。

请生成以下JSON格式的信息（只返回JSON，不要有其他内容）：

{{
    "name": "{name}",
    "gender": "中性",
    "age": 建国/成立年限（如"5000"表示5000年文明史）,
    "mbti": "16种MBTI之一，要符合该国的整体国民性格特征",
    "background": {{
        "gender": "中性",
        "age": 建国/成立年限数字,
        "occupation": "国家/组织性质，如'世界大国'、'发展中国家'等",
        "education": "主要政治体制",
        "hometown": "首都/总部所在地",
        "description": "200字左右的背景描述，包括国家历史、政治制度、文化特点、当前处境等"
    }},
    "appearance": "150字左右的描述，包括疆域特征、首都地标、国家象征等",
    "personality_traits": ["3-5个性格关键词，体现国民性格"],
    "core_values": ["3-5个核心价值观/治国理念"],
    "famous_quotes": ["2-3句国家宣言或名言"],
    "key_memories": [
        "3-5条重要历史事件，每条50字左右"
    ]
}}

要求：
1. 把国家/组织当做一个"角色"来描述
2. MBTI要符合该国/组织的整体性格特征
3. 关键记忆要选取最重要的历史事件
4. 只返回JSON格式，不要有任何前缀或解释文字"""


def _parse_historical_agent_response(response: str, name: str, era: str) -> Dict:
    """解析LLM返回的历史人物响应"""
    try:
        # 提取JSON
        json_str = _extract_json(response)
        data = json.loads(json_str)

        # 验证必需字段
        required = ["name", "gender", "mbti", "background", "appearance"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        # 补充默认值
        if "age" not in data:
            data["age"] = 30

        if "personality_traits" not in data:
            data["personality_traits"] = ["智慧", "果断", "勇敢"]

        if "core_values" not in data:
            data["core_values"] = ["统一", "强大", "传承"]

        if "famous_quotes" not in data:
            data["famous_quotes"] = ["天下统一"]

        if "key_memories" not in data:
            data["key_memories"] = [f"建立了{name}的伟大功业"]

        return data

    except Exception as e:
        print(f"解析历史人物响应失败: {e}，使用默认数据")
        return _get_default_historical_agent(name, era)


def _parse_country_agent_response(response: str, name: str, country_type: str) -> Dict:
    """解析LLM返回的国家响应"""
    try:
        json_str = _extract_json(response)
        data = json.loads(json_str)

        # 验证必需字段
        required = ["name", "mbti", "background", "appearance"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        # 补充默认值
        if "age" not in data:
            data["age"] = 100

        data["gender"] = "中性"

        if "personality_traits" not in data:
            data["personality_traits"] = ["勤劳", "智慧", "团结"]

        if "core_values" not in data:
            data["core_values"] = ["和平", "发展", "合作"]

        if "famous_quotes" not in data:
            data["famous_quotes"] = ["和平共处五项原则"]

        if "key_memories" not in data:
            data["key_memories"] = [f"{name}建立并发展壮大"]

        return data

    except Exception as e:
        print(f"解析国家响应失败: {e}，使用默认数据")
        return _get_default_country_agent(name, country_type)


def _extract_json(text: str) -> str:
    """从文本中提取JSON字符串"""
    # 尝试找到JSON开始和结束
    start = text.find('{')
    end = text.rfind('}') + 1

    if start >= 0 and end > start:
        return text[start:end]

    # 尝试找数组
    start = text.find('[')
    end = text.rfind(']') + 1

    if start >= 0 and end > start:
        return text[start:end]

    raise ValueError("No JSON found in response")


def _create_agent_from_data(data: Dict, config: Dict = None) -> BaseAgent:
    """从数据字典创建Agent"""
    config = config or {}

    agent_id = str(uuid.uuid4())[:8]
    vector_store_dir = f"agent/history/{agent_id}/vector_store"

    # 构建background字典
    background = data.get("background", {})
    if isinstance(background, str):
        # 如果是字符串，转换为字典
        background = {
            "gender": data.get("gender", "未知"),
            "age": data.get("age", 30),
            "occupation": "历史人物",
            "education": "传统教育",
            "hometown": data.get("background", {}).get("hometown", "未知") if isinstance(data.get("background"), dict) else "未知",
            "description": str(background)
        }

    # 创建Agent
    agent = BaseAgent(
        id=agent_id,
        name=data.get("name", "未知"),
        gender=data.get("gender", "未知"),
        age=data.get("age", 30),
        mbti=data.get("mbti", "INTJ"),
        background=background,
        appearance=data.get("appearance", "外表普通"),
        vector_store_dir=vector_store_dir
    )

    # 保存身份
    agent.save_identity()

    # 保存初始记忆
    memories = data.get("key_memories", [])
    for memory in memories:
        agent.add_memory(memory, is_long_term=True)

    # 保存额外属性
    if "personality_traits" in data:
        agent.personality_traits = data["personality_traits"]
    if "core_values" in data:
        agent.core_values = data["core_values"]
    if "famous_quotes" in data:
        agent.famous_quotes = data["famous_quotes"]

    return agent


def _generate_mock_historical_agent(name: str, era: str) -> str:
    """生成模拟的历史人物数据（用于mock模式）"""
    import random

    mbti_list = ["INTJ", "INTP", "ENTJ", "ENFJ", "INFJ", "ENFP"]
    occupations = ["君主", "思想家", "将军", "政治家", "文人"]
    personalities = ["雄才大略", "深思熟虑", "果敢坚定", "仁爱宽厚"]

    return json.dumps({
        "name": name,
        "gender": random.choice(["男", "女"]),
        "age": random.randint(30, 60),
        "mbti": random.choice(mbti_list),
        "background": {
            "gender": "男" if random.random() > 0.1 else "女",
            "age": random.randint(30, 60),
            "occupation": random.choice(occupations),
            "education": "传统教育",
            "hometown": "华夏",
            "description": f"{name}是{era or '中国古代'}的著名人物，以其卓越的智慧和能力著称。"
        },
        "appearance": f"{name}举止端庄，气质不凡，眉宇间透露出智慧与威严。",
        "personality_traits": random.sample(personalities, 3),
        "core_values": ["仁政", "统一", "传承"],
        "famous_quotes": ["天下统一", "以德服人"],
        "key_memories": [
            f"{name}年少时便展现出过人的智慧",
            f"{name}成就了一番伟大事业",
            f"{name}的事迹流传千古"
        ]
    }, ensure_ascii=False)


def _generate_mock_country(name: str, country_type: str) -> str:
    """生成模拟的国家数据（用于mock模式）"""
    import random

    mbti_list = ["ENTJ", "ESTJ", "ESFJ", "ISFJ", "INFJ"]
    personalities = ["勤劳勇敢", "爱好和平", "团结奋进", "包容开放"]

    return json.dumps({
        "name": name,
        "gender": "中性",
        "age": random.randint(50, 5000),
        "mbti": random.choice(mbti_list),
        "background": {
            "gender": "中性",
            "age": random.randint(50, 5000),
            "occupation": "国家",
            "education": "政治体制",
            "hometown": "首都",
            "description": f"{name}是一个历史悠久的{'国家' if country_type == 'nation' else '组织'}，具有独特的文化和传统。"
        },
        "appearance": f"{name}地域辽阔，文化多元，国家象征意义深远。",
        "personality_traits": random.sample(personalities, 3),
        "core_values": ["和平", "发展", "合作"],
        "famous_quotes": ["和平共处", "互利共赢"],
        "key_memories": [
            f"{name}的建立和发展历程波澜壮阔",
            f"{name}在历史长河中留下了灿烂的文明"
        ]
    }, ensure_ascii=False)


def _get_default_historical_agent(name: str, era: str) -> Dict:
    """获取默认历史人物数据"""
    return {
        "name": name,
        "gender": "男",
        "age": 40,
        "mbti": "ENTJ",
        "background": {
            "gender": "男",
            "age": 40,
            "occupation": "历史人物",
            "education": "传统教育",
            "hometown": "华夏",
            "description": f"{name}是{era or '古代'}的著名人物，以其卓越的智慧和能力著称。"
        },
        "appearance": f"{name}举止端庄，气质不凡，眉宇间透露出智慧与威严。",
        "personality_traits": ["雄才大略", "深思熟虑", "果敢坚定"],
        "core_values": ["仁政", "统一", "传承"],
        "famous_quotes": ["天下统一"],
        "key_memories": [f"{name}建立了不朽的功业"]
    }


def _get_default_country_agent(name: str, country_type: str) -> Dict:
    """获取默认国家数据"""
    return {
        "name": name,
        "gender": "中性",
        "age": 1000,
        "mbti": "ENTJ",
        "background": {
            "gender": "中性",
            "age": 1000,
            "occupation": "国家",
            "education": "政治体制",
            "hometown": "首都",
            "description": f"{name}是一个重要的{'国家' if country_type == 'nation' else '组织'}。"
        },
        "appearance": f"{name}具有独特的国家特征和文化传统。",
        "personality_traits": ["勤劳勇敢", "爱好和平", "团结奋进"],
        "core_values": ["和平", "发展", "合作"],
        "famous_quotes": ["和平共处五项原则"],
        "key_memories": [f"{name}建立并发展壮大"]
    }


# 命令行接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生成历史人物或国家Agent")
    parser.add_argument("--name", "-n", required=True, help="人物/国家名称")
    parser.add_argument("--type", "-t", choices=["person", "country"], default="person", help="类型")
    parser.add_argument("--era", "-e", help="时代背景（仅人物）")
    parser.add_argument("--desc", "-d", help="额外描述")

    args = parser.parse_args()

    if args.type == "person":
        agent = create_historical_agent(args.name, args.era, args.desc)
    else:
        agent = create_country_agent(args.name, description=args.desc)

    print(f"\n已创建Agent: {agent.name}")
    print(f"MBTI: {agent.mbti}")
    print(f"背景: {agent.background.get('description', '')[:100]}...")
    print(f"外貌: {agent.appearance[:50]}...")
    print(f"Agent ID: {agent.id}")
