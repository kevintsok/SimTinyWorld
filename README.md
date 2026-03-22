# 智能体社会模拟系统

一个基于Python的多智能体社会模拟引擎，让历史人物复活、穿越时空对话、重写人类命运。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/LLM-Qwen|OpenAI|DeepSeek-green.svg" alt="LLM">
  <img src="https://img.shields.io/badge/Memory-FAISS向量库-orange.svg" alt="FAISS">
</p>

---

## 🔥 穿越时空，与历史人物对话

**秦始皇** vs **希特勒** vs **拿破仑** — 谁是最伟大的征服者？

**诸葛亮** vs **克劳塞维茨** vs **孙子** — 谁是最智慧的军事家？

在这个模拟器中，你可以创造任何历史人物，让他们穿越时空在同一舞台上交锋！

## ✨ 功能特点

### 🤖 智能Agent系统
- **MBTI人格** — 每个Agent都有独特的16型人格，影响行为模式
- **记忆系统** — 短期记忆（日常交互）+ 长期记忆（人生经历），基于FAISS向量检索
- **财富系统** — 时间、社交、健康、精神、金钱五维状态
- **心情波动** — MBTI影响情绪反应，阳光开朗或深沉内敛

### 🌍 穿越历史的预设场景

| 场景 | 时代 | 参与者 |
|------|------|--------|
| 秦始皇一统天下 | 公元前221年 | 秦始皇、楚国使者、赵国使者、魏国使者 |
| 三国鼎立 | 公元220年 | 刘备、孙权、曹丕、诸葛亮 |
| 十字军东征 | 公元1096年 | 教皇乌尔班二世、拜占庭皇帝、戈弗雷爵士、塞尔柱苏丹 |
| 法国大革命 | 公元1789年 | 路易十六、罗伯斯庇尔、拉法耶特、玛丽王后 |
| 雅尔塔会议 | 公元1945年 | 罗斯福、丘吉尔、斯大林 |
| 明治维新 | 公元1868年 | 明治天皇、西乡隆盛、木户孝允、德川庆喜 |
| 尼克松访华 | 公元1972年 | 尼克松、周恩来、毛泽东 |
| 丝绸之路 | 公元100年 | 汉朝使节、罗马商人、波斯贵族、佛教僧侣 |
| 马丁·路德改革 | 公元1517年 | 马丁·路德、台彻尔、教皇利奥十世、伊拉斯谟 |
| 罗马的陨落 | 公元410年 | 霍诺留皇帝、阿拉里克、斯提利科、罗马元老 |

### 🎮 游戏风格可视化
- **2D俯视角地图** — RPG游戏风格
- **实时观察** — Agent移动、对话气泡、状态变化一目了然
- **Agent详情面板** — MBTI、财富、记忆、心情全面展示

### 📜 JSON场景自定义
用JSON文件定义任何场景，无需编程：

```json
{
  "name": "我的历史场景",
  "type": "debate",
  "agents": [
    {
      "name": "恺撒",
      "role": "罗马独裁官",
      "MBTI": "ENTJ",
      "goals": ["统一罗马", "征服高卢"]
    }
  ],
  "events": [
    {"trigger": {"type": "round", "value": 3}, "content": "决战时刻！"}
  ]
}
```

---

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 创建历史人物

```python
from agent.historical import create_historical_agent

# 创造秦始皇
qin = create_historical_agent("秦始皇", era="战国时期")
print(f"MBTI: {qin.mbti}")  # ENTJ - 天生的领导者
```

### 运行历史场景

```bash
# 秦始皇一统天下
python main.py --scenario json --scenario-file scenarios/qin_shihuang.json --fast

# 三国鼎立
python main.py --scenario json --scenario-file scenarios/three_kingdoms.json --fast

# 雅尔塔会议（罗斯福/丘吉尔/斯大林）
python main.py --scenario json --scenario-file scenarios/wwii_conference.json --fast
```

### 自定义场景

```bash
python main.py --scenario json --scenario-file your_scenario.json --agents 5 --rounds 10 --fast
```

### 完整模拟（需要API密钥）

```bash
# 设置API密钥
export DASHSCOPE_API_KEY="your-api-key"

# 运行完整模拟
python main.py --scenario json --scenario-file scenarios/qin_shihuang.json --agents 6 --rounds 8
```

---

## 📂 场景文件

| 文件 | 描述 |
|------|------|
| `scenarios/qin_shihuang.json` | 秦始皇召集六国使者 |
| `scenarios/three_kingdoms.json` | 魏蜀吴三国博弈 |
| `scenarios/crusades.json` | 十字军东征 |
| `scenarios/french_revolution.json` | 法国大革命 |
| `scenarios/wwii_conference.json` | 雅尔塔会议 |
| `scenarios/meiji_restoration.json` | 明治维新 |
| `scenarios/us_china_nixon.json` | 尼克松访华 |
| `scenarios/silkroad.json` | 丝绸之路贸易 |
| `scenarios/protestant_reformation.json` | 马丁·路德宗教改革 |
| `scenarios/roman_fall.json` | 罗马的陨落 |
| `scenarios/dawn_of_civilization.json` | 人类最早的文明 |

---

## 🎯 核心概念

### Agent
- **MBTI** — 16种性格类型，影响对话风格和行为模式
- **记忆** — 基于FAISS的向量检索，Agent能记住历史交互
- **财富** — 五维状态系统，健康/金钱/社交等
- **心情** — 根据事件动态变化

### 场景类型
- **dialogue** — 自由对话
- **debate** — 辩论竞争
- **cooperation** — 协作任务
- **emergency** — 突发事件

### 评估系统
每个场景结束后的综合评分：
- **论点强度** — 论证是否有说服力
- **合作指数** — 促进团队协作程度
- **目标达成** — 个人目标完成度

---

## 🏗️ 架构

```
BaseEntity (ABC)
    └── BaseAgent (ABC)
            └── agent/base_agent.py::BaseAgent  (MBTI, Memory, Wealth)

BaseEnvironment (ABC)
            └── environment/world.py::World

BaseScenario (ABC)
            └── JSONScenario (支持JSON配置)
```

---

## 🤝 扩展开发

### 添加新场景（Python）
```python
class MyScenario(BaseScenario):
    def setup(self): ...
    def get_prompt_for_agent(self, agent, context): ...
    def evaluate_action(self, agent, action): ...
    def step(self, agents, environment, step): ...
```

### 添加新场景（JSON）
只需创建JSON文件，无需编程！参考 `scenarios/` 目录下的示例。

---

## 📝 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--scenario` | 场景类型 | daily_life |
| `--scenario-file` | JSON场景文件 | - |
| `--agents` | Agent数量 | 20 |
| `--rounds` | 模拟轮数 | 5 |
| `--locations` | 地点数量 | 3 |
| `--engine` | LLM引擎 | qwen |
| `--fast` | 快速测试模式 | - |
| `--visual` | 可视化模式 | - |

---

<p align="center">
让历史重演，让思想碰撞，让AI成为你的历史实验室。
</p>
