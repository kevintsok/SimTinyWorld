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

# 导入模拟框架
from simulation import SimulationEngine, get_scenario
from simulation.scenarios.daily_life import DailyLifeScenario

# 导入智能体创建/加载模块
from agent.create import create_new_agents, load_existing_agents, clean_environment

# LLM引擎懒加载
from llm_engine.factory import get_global_engine, has_global_engine


def init_llm_engine(engine_type: str = None):
    """初始化LLM引擎（懒加载）

    Args:
        engine_type: 引擎类型，默认为None（从环境变量或配置获取）

    Returns:
        str: 使用的引擎类型
    """
    if has_global_engine():
        # 引擎已初始化，直接返回
        return os.environ.get("DEFAULT_LLM_ENGINE", "qwen")

    print("\n正在初始化LLM引擎...")

    # 获取引擎实例
    try:
        engine = get_global_engine(engine_type)

        if engine.mock_mode:
            print(f"引擎 {engine_type or 'qwen'} 运行在模拟模式")
        else:
            print(f"引擎 {engine_type or 'qwen'} 初始化成功")

        return engine_type or os.environ.get("DEFAULT_LLM_ENGINE", "qwen")

    except Exception as e:
        print(f"引擎初始化失败: {e}")
        print("将使用模拟模式继续...")

        # 尝试使用模拟模式创建引擎
        try:
            engine_type = engine_type or "qwen"
            get_global_engine(engine_type, mock_mode=True)
            return engine_type
        except:
            return None


def create_mock_agents(num_agents=20):
    """创建模拟智能体（用于快速测试）

    Args:
        num_agents: 要创建的智能体数量
    """
    from agent.base_agent import BaseAgent

    # 常见中文姓名
    first_names = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴"]
    last_names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋"]

    # MBTI类型
    mbti_types = ["ENFJ", "ENFP", "ENTJ", "ENTP", "ESFJ", "ESFP", "ESTJ", "ESTP",
                  "INFJ", "INFP", "INTJ", "INTP", "ISFJ", "ISFP", "ISTJ", "ISTP"]

    agents = []
    for i in range(num_agents):
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first}{last}{i}"
        gender = random.choice(["男", "女"])
        mbti = random.choice(mbti_types)

        agent = BaseAgent(
            id=f"agent_{i}",
            name=name,
            gender=gender,
            age=random.randint(20, 50),
            mbti=mbti,
            background=f"职业: {random.choice(['工程师', '教师', '医生', '销售', '设计师'])}",
            appearance=f"外貌: 普通身高, {random.choice(['英俊', '清秀', '普通'])}",
            init_wealth={
                "time": 0.0,
                "social": 0.0,
                "health": 0.5,
                "mental": 0.5,
                "money": random.randint(10000, 100000)
            }
        )

        # 添加一些初始记忆
        agent.add_memory("今天是我在这个世界的第一天。")
        agent.add_memory(f"我叫{name}，今年{agent.age}岁。")

        # 添加daily_plan属性（用于场景中的移动）
        agent.daily_plan = []
        agent.plan_index = 0
        agent.current_plan_index = 0
        agent.status = "空闲"
        agent.current_plan = None

        agents.append(agent)

    return agents


def run_simulation(agents, args):
    """使用SimulationEngine运行模拟

    Args:
        agents: 智能体列表
        args: 命令行参数
    """
    print("\n=== 初始化模拟环境 ===")

    # 创建环境
    descriptions = EnvironmentDescriptions()

    if args.fast:
        # 快速模式：跳过环境描述生成
        descriptions.initialize_environment(force=False)
    else:
        descriptions.initialize_environment(force=not args.continue_mode)

    world = World(visual_mode=args.visual, location_count=args.locations)
    world.init_locations(descriptions.default_locations[:args.locations])

    # 创建场景配置
    scenario_config = {
        "days": 3,
        "rounds_per_day": args.rounds,
        "max_participants": args.max_participants,
        "fast_mode": args.fast
    }

    # 创建场景
    scenario = get_scenario(args.scenario, scenario_config, args.scenario_file)

    # 根据场景类型计算默认步数
    if args.scenario == "debate":
        # debate: 每个agent每轮发言一次，总步数 = agents * rounds
        default_steps = args.agents * args.rounds
    else:
        # daily_life等: steps = rounds * days
        default_steps = args.rounds * 3

    # 创建模拟引擎
    engine = SimulationEngine(
        scenario=scenario,
        environment=world,
        config={"default_steps": default_steps}
    )

    # 添加智能体
    for agent in agents:
        location = random.choice(list(world.locations.keys()))
        engine.add_agent(agent, location)

    # 运行模拟
    print("\n=== 开始模拟 ===")
    result = engine.run()

    print("\n=== 模拟结束 ===")
    print(f"总步数: {result.get('steps', 0)}")
    print(f"日志已保存到logs目录")

    return agents


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
    parser.add_argument("--max-participants", type=int, default=5,
                      help="一次对话最多参与者数量，默认为4")
    parser.add_argument("--reinit-env", action="store_true", default=False,
                      help="是否重新初始化环境描述，默认为否")
    parser.add_argument("--locations", type=int, default=3,
                      help="生成的地点数量，默认为2个")
    parser.add_argument("--skip-verify", action="store_true", default=False,
                      help="跳过LLM引擎验证")
    parser.add_argument("--fast", action="store_true", default=False,
                      help="快速测试模式，跳过LLM调用用于快速验证流程")
    parser.add_argument("--engine", type=str, default=None,
                      help="指定使用的LLM引擎类型（qwen, openai, deepseek）")
    parser.add_argument("--scenario", type=str, default="daily_life",
                      choices=["daily_life", "emergency", "debate", "json"],
                      help="模拟场景类型")
    parser.add_argument("--scenario-file", type=str, default=None,
                      help="JSON场景文件路径（用于json场景类型）")

    args = parser.parse_args()

    # 处理模式设置 - 如果使用了--continue/-c参数，将mode设为"continue"
    if args.continue_mode:
        args.mode = "continue"

    print(f"以 {args.mode} 模式启动模拟...")
    print(f"使用{'可视化' if args.visual else '终端'}模式")
    print(f"智能体数量: {args.agents}")
    print(f"地点数量: {args.locations}")
    print(f"对话最大参与者数量: {args.max_participants}")
    print(f"场景类型: {args.scenario}")

    # 初始化LLM引擎（懒加载）
    # 如果指定了引擎，使用该引擎；否则从环境变量或默认qwen获取
    if args.engine:
        os.environ["DEFAULT_LLM_ENGINE"] = args.engine

    if not args.skip_verify:
        init_llm_engine(args.engine)
    else:
        # 跳过验证时，直接以模拟模式初始化
        print("\n跳过LLM验证，使用模拟模式...")
        get_global_engine(args.engine, mock_mode=True)

    if args.mode == "new":
        # 重新开始模式：清理环境并创建新的智能体
        print("清理环境...")
        clean_environment()

        if args.fast:
            # 快速模式：创建模拟智能体
            print(f"创建 {args.agents} 个模拟智能体（快速模式）...")
            agents = create_mock_agents(args.agents)
        else:
            print(f"创建 {args.agents} 个新的智能体...")
            agents = create_new_agents(args.agents)
    else:
        # 继续模式：加载已存在的智能体
        print("加载现有智能体...")
        agents = load_existing_agents(args.agents)

    # 运行模拟
    agents = run_simulation(agents, args)

    print("\n模拟完成")
    print("所有模拟日志和对话已保存到logs目录")


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
