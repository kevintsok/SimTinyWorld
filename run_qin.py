#!/usr/bin/env python3
"""
运行秦始皇模拟 - 快速测试版本
"""
import sys
import os
import random

# 设置快速模式
os.environ['DEFAULT_LLM_ENGINE'] = 'qwen'

from agent.historical import create_historical_agent
from agent.create import create_new_agents, clean_environment
from simulation import SimulationEngine, get_scenario
from environment.world import World
from environment.environment_descriptions import EnvironmentDescriptions
from llm_engine.factory import get_global_engine

def main():
    # 初始化mock引擎
    print("初始化模拟引擎...")
    engine = get_global_engine(mock_mode=True)
    print(f"引擎模式: {'模拟模式' if engine.mock_mode else '真实模式'}")

    # 清理环境
    print("\n清理环境...")
    clean_environment()

    # 创建秦始皇
    print("\n=== 创建秦始皇 ===")
    qin = create_historical_agent("秦始皇", era="战国时期")
    print(f"Agent ID: {qin.id}")
    print(f"名字: {qin.name}")
    print(f"MBTI: {qin.mbti}")
    print(f"职业: {qin.background.get('occupation')}")
    print(f"背景: {qin.background.get('description', '')[:150]}...")

    # 创建环境
    print("\n=== 初始化环境 ===")
    descriptions = EnvironmentDescriptions()
    descriptions.initialize_environment(force=True)

    world = World(visual_mode=False, location_count=3)
    world.init_locations(descriptions.default_locations[:3])

    print(f"创建了 {len(world.locations)} 个位置")
    for loc_name in world.locations:
        print(f"  - {loc_name}")

    # 创建场景
    print("\n=== 创建场景 ===")
    scenario = get_scenario("daily_life", {"rounds_per_day": 3, "fast_mode": True})
    print(f"场景类型: daily_life")

    # 创建模拟引擎
    sim_engine = SimulationEngine(
        scenario=scenario,
        environment=world,
        config={"default_steps": 6}
    )

    # 添加秦始皇
    location = random.choice(list(world.locations.keys()))
    sim_engine.add_agent(qin, location)
    print(f"\n秦始皇添加到位置: {location}")

    # 添加其他智能体
    print("\n=== 创建其他智能体 ===")
    others = create_new_agents(3)
    for agent in others:
        loc = random.choice(list(world.locations.keys()))
        sim_engine.add_agent(agent, loc)
        print(f"  {agent.name} 添加到位置: {loc}")

    # 运行模拟
    print("\n" + "="*50)
    print("开始模拟")
    print("="*50)
    result = sim_engine.run()

    # 显示结果
    print("\n" + "="*50)
    print("模拟结束")
    print("="*50)
    print(f"总步数: {result.get('steps', 0)}")

    # 显示秦始皇状态
    print("\n=== 秦始皇状态 ===")
    print(f"心情: {qin.mood['description']} ({qin.mood['value']:.2f})")
    print(f"状态: {qin.status}")
    print(f"财富:")
    print(f"  时间: {qin.wealth.get('time', 0):.2f}")
    print(f"  社交: {qin.wealth.get('social', 0):.2f}")
    print(f"  健康: {qin.wealth.get('health', 0):.2f}")
    print(f"  精神: {qin.wealth.get('mental', 0):.2f}")
    print(f"  金钱: {qin.wealth.get('money', 0):.0f}")
    print(f"\n记忆:")
    print(f"  短期记忆: {len(qin.short_term_memory)} 条")
    print(f"  长期记忆: {len(qin.long_term_memory)} 条")

    # 显示最近的记忆
    if qin.short_term_memory:
        print(f"\n秦始皇的近期记忆:")
        for i, mem in enumerate(qin.short_term_memory[-3:], 1):
            print(f"  {i}. {mem[:80]}...")

if __name__ == "__main__":
    main()
