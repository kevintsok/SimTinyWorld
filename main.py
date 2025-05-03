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
# 导入新的模块
from simulate import run_simulation, update_agents_wealth
from agent.create import create_new_agents, load_existing_agents, clean_environment

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
    agents = run_simulation(agents, rounds=args.rounds, visual_mode=args.visual, 
                  max_conversation_participants=args.max_participants,
                  environment_init=not args.continue_mode,
                  location_count=args.locations)
    
    print("\n模拟结束")
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