# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent social simulation system in Python. Agents with distinct personalities (MBTI), backgrounds, and memories interact in a virtual environment with multiple locations. Supports multiple LLM backends (Qwen, OpenAI, DeepSeek).

## Commands

```bash
# Run simulation
python main.py

# Fast test mode (mock LLM calls)
python main.py --fast --agents 3 --rounds 2

# Continue existing simulation
python main.py --mode continue

# Specify LLM engine
python main.py --engine qwen   # default
python main.py --engine openai
python main.py --engine deepseek

# Custom parameters
python main.py --agents 20 --rounds 5 --locations 3
```

## Architecture

### Core Abstraction Hierarchy

```
BaseEntity (ABC)           # simulation/base.py
    └── BaseAgent (ABC)    # simulation/base.py
            └── agent/base_agent.py::BaseAgent  (concrete agent with MBTI, memory, wealth)

BaseEnvironment (ABC)      # simulation/base.py
            └── environment/world.py::World    (concrete environment with locations)

BaseScenario (ABC)         # simulation/scenarios/base.py
            └── DailyLifeScenario              (concrete scenario)
```

### Module Structure

- **simulation/** - Framework core: `SimulationEngine`, abstract base classes
- **simulation/scenarios/** - Scenario implementations (daily_life, emergency, geopolitics, debate)
- **agent/** - Agent implementation: `BaseAgent` with MBTI personality, memory system, wealth tracking
- **environment/** - Environment: `World` with `Location` entities, spatial relationships
- **llm_engine/** - LLM backends: factory pattern with lazy loading for Qwen/OpenAI/DeepSeek

### Key Patterns

1. **Factory + Singleton**: `LLMEngineFactory.create_engine()` creates engines; `get_global_engine()` provides singleton access
2. **Lazy Loading**: Engine classes imported only when first used via `_get_engine_class()`
3. **Scenario-Based**: `SimulationEngine` runs scenarios that inherit from `BaseScenario`

### Adding New Scenarios

1. Create `simulation/scenarios/your_scenario.py` extending `BaseScenario`
2. Implement: `setup()`, `get_prompt_for_agent()`, `evaluate_action()`, `step()`
3. Register in `simulation/scenarios/__init__.py::SCENARIOS`
4. Use via `python main.py --scenario your_scenario`

### Adding New LLM Engines

1. Create engine class extending `BaseLLMEngine` in `llm_engine/`
2. Implement `generate()`, `chat()`, `mock_mode` property
3. Register in `llm_engine/factory.py::_get_engine_class()`

## Configuration

API keys via environment variables or `llm_engine/config/api_keys.json`:
- `DASHSCOPE_API_KEY` (Qwen)
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`

## Dependencies

Key packages: dashscope, openai, faiss-cpu, langchain, pygame (visualization), colorama
