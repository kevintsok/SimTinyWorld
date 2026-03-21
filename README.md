# 智能体社会模拟系统

这是一个基于Python的智能体社会模拟系统，可以创建具有不同性格和背景的智能体，并在虚拟环境中进行交互。

## 功能特点

- 创建具有独特性格（MBTI）和背景的智能体
- 智能体具有长期记忆和短期记忆
- 使用 FAISS 向量数据库进行记忆检索
- 支持多种 LLM 引擎：通义千问、OpenAI、DeepSeek
- 虚拟环境包含多个可交互的场所
- 智能体可以在环境中移动和互动
- 财富系统：时间、社交、健康、精神、金钱

## 安装要求

1. Python 3.8+
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 环境配置

1. 配置 API 密钥（可选，支持多引擎）：

方式一：编辑 `llm_engine/config/api_keys.json`
```json
{
  "OPENAI": "your-openai-api-key",
  "QWEN": "your-qwen-api-key",
  "DEEPSEEK": "your-deepseek-api-key"
}
```

方式二：设置环境变量
```bash
export DASHSCOPE_API_KEY="your-qwen-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

## 使用方法

```bash
# 运行模拟（默认使用 qwen 引擎）
python main.py

# 继续运行已有的智能体
python main.py --mode continue

# 自定义参数
python main.py --agents 20 --rounds 5 --locations 3

# 指定 LLM 引擎
python main.py --engine qwen    # 通义千问（默认）
python main.py --engine openai  # OpenAI
python main.py --engine deepseek # DeepSeek

# 跳过 LLM 验证（使用模拟模式）
python main.py --skip-verify
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式：`new` 或 `continue` | `new` |
| `--agents` | 智能体数量 | 20 |
| `--rounds` | 每天模拟轮数 | 5 |
| `--locations` | 地点数量 | 3 |
| `--max-participants` | 每次对话最大参与者 | 5 |
| `--engine` | LLM 引擎类型 | qwen |
| `--skip-verify` | 跳过 LLM 验证 | False |
| `--visual` | 启用可视化模式 | False |

## 项目结构

```
.
├── main.py                 # 主入口
├── simulate.py             # 模拟核心逻辑
├── requirements.txt        # 依赖
├── agent/                  # 智能体模块
│   ├── base_agent.py       # 智能体基类
│   ├── create.py           # 智能体创建/加载
│   └── interact.py         # 对话交互
├── environment/            # 环境模块
│   ├── world.py            # 世界管理
│   ├── layout.py           # 环境布局
│   └── environment_descriptions.py
├── llm_engine/             # LLM 引擎
│   ├── factory.py          # 引擎工厂
│   ├── base.py             # 基类
│   ├── qwen.py             # 通义千问
│   ├── openai.py           # OpenAI
│   ├── deepseek.py         # DeepSeek
│   └── config/             # 配置
└── utils/
    └── logger.py           # 日志记录
```

## 智能体特性

- 每个智能体都有唯一的 ID
- 随机生成的 MBTI 性格类型
- 随机生成的背景信息（年龄、职业、教育程度等）
- 长期记忆和短期记忆系统
- 基于记忆的对话生成能力
- 心情状态和财富系统

## 环境特性

- 多个可交互场所（公司、公园、医院、学校、餐厅等）
- 场所之间的连接关系
- 智能体移动和互动机制
- 多人对话系统

## 注意事项

- 确保有足够的磁盘空间存储智能体记忆
- 需要稳定的网络连接以使用 LLM API
- 建议在运行前检查 API 密钥配置
