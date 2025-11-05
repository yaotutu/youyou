# YouYou 快速开始指南

## 第一步: 配置环境

1. 复制环境变量模板:
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件,填写你的 OpenAI API 配置:
```bash
# 必填项
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# 可选配置
ROUTER_MODEL=gpt-3.5-turbo
AGENT_MODEL=gpt-4
```

**注意**: 
- 如果使用 OpenAI 兼容接口(如 Ollama、Azure 等),修改 `OPENAI_API_BASE`
- `ROUTER_MODEL` 用于意图识别(推荐用便宜的模型)
- `AGENT_MODEL` 用于执行任务(推荐用准确的模型)

## 第二步: 安装依赖

依赖已经通过 `uv sync` 安装完成。如果需要重新安装:

```bash
uv sync
```

## 第三步: 运行

```bash
uv run youyou
```

## 使用示例

### 物品位置记忆

```
你: 钥匙在客厅桌上
YouYou: 好的,我已经记住了,钥匙在客厅桌上。

你: 钥匙在哪?
YouYou: 钥匙在客厅桌上。

你: 我记录了哪些物品?
YouYou: 你记录了以下物品:
1. 钥匙 - 客厅桌上
...
```

### 普通对话

```
你: 你好
YouYou: 你好!我是 YouYou,你的个人助理。有什么可以帮你的吗?
```

## 可用命令

- `/help` - 显示帮助
- `/exit` - 退出程序
- `/clear` - 清空屏幕
- `/config` - 显示配置信息

## 数据存储

所有数据存储在 `data/` 目录:
- `data/qdrant/` - 向量数据库(物品记忆等)

## 常见问题

### Q: 提示 "未设置 OPENAI_API_KEY"
A: 确保已经创建 `.env` 文件并填写了 `OPENAI_API_KEY`

### Q: 记忆系统初始化失败
A: 首次运行时 mem0 会下载向量模型,需要等待几分钟。确保网络连接正常。

### Q: 如何使用本地模型?
A: 使用 Ollama 等工具启动本地模型,然后修改 `.env`:
```
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama  # 任意值
ROUTER_MODEL=qwen2.5:7b
AGENT_MODEL=qwen2.5:14b
```

## 下一步

体验完基础功能后,可以:
1. 查看 [README.md](README.md) 了解完整功能
2. 探索代码结构,尝试添加新的 Agent
3. 反馈问题和建议

祝使用愉快! 🎉
