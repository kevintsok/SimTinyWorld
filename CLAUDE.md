# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent social simulation system where agents with distinct personalities (MBTI), backgrounds, and memories interact in a virtual environment. Supports multiple LLM backends (Qwen, OpenAI, DeepSeek) with FAISS vector storage for memory retrieval.

## Commands

```bash
# Run simulation
python main.py

# Fast test mode (mock LLM calls, skip API verification)
python main.py --fast --agents 3 --rounds 2

# Skip LLM verification and use mock mode directly
python main.py --skip-verify

# Continue existing simulation
python main.py --mode continue

# Specify LLM engine
python main.py --engine qwen   # default
python main.py --engine openai
python main.py --engine deepseek

# Custom parameters
python main.py --agents 20 --rounds 5 --locations 3

# Specify scenario
python main.py --scenario daily_life  # default
```

## Architecture

### Three Core Abstraction Hierarchies

**Agent System** (`simulation/base.py` → `agent/base_agent.py`):
- `BaseEntity` (ABC) - base for all entities
- `BaseAgent` (ABC) - adds think(), perceive(), act(), memory system, mood, wealth
- `BaseAgent` (concrete) - MBTI personality, long/short-term memory with FAISS, sleep cycle

**Environment System** (`simulation/base.py` → `environment/world.py`):
- `BaseEnvironment` (ABC) - add_entity(), remove_entity(), get_neighbors(), tick()
- `World` (concrete) - manages Location entities with spatial relationships, optional pygame visualization

**Scenario System** (`simulation/scenarios/base.py` → `simulation/scenarios/daily_life.py`):
- `BaseScenario` (ABC) - setup(), get_prompt_for_agent(), evaluate_action(), step()
- `DailyLifeScenario` - daily planning, movement, conversations, wealth/mood updates

### Module Structure

| Module | Purpose |
|--------|---------|
| `simulation/` | Core engine and abstract base classes |
| `simulation/scenarios/` | Scenario implementations (only `daily_life` currently active) |
| `agent/` | `BaseAgent` with MBTI, memory (FAISS), wealth tracking |
| `environment/` | `World` with `Location` entities |
| `llm_engine/` | Factory + lazy loading for Qwen/OpenAI/DeepSeek |

### Key Patterns

- **Factory + Singleton**: `LLMEngineFactory.create_engine()` + `get_global_engine()`
- **Lazy Loading**: Engine classes imported on first use via `_get_engine_class()`
- **Thread-safe Simulation**: `SimulationEngine` uses locks for agent management

### Adding New Scenarios

1. Create `simulation/scenarios/your_scenario.py` extending `BaseScenario`
2. Implement: `setup()`, `get_prompt_for_agent()`, `evaluate_action()`, `step()`
3. Register in `simulation/scenarios/__init__.py::SCENARIOS`
4. Use via `python main.py --scenario your_scenario`

### Adding New LLM Engines

1. Create engine class in `llm_engine/` extending `BaseLLMEngine`
2. Implement `generate()`, `get_embeddings()`, `mock_mode` property
3. Add lazy import in `llm_engine/factory.py::_get_engine_class()`

## Configuration

API keys via environment variables or `llm_engine/config/api_keys.json`:
- `DASHSCOPE_API_KEY` (Qwen), `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`
