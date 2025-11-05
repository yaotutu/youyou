# YouYou 故障排查指南

## 问题 1: "Model does not exist" 错误

### 症状
```
搜索失败: Error code: 400 - {'code': 20012, 'message': 'Model does not exist. Please check it carefully.', 'data': None}
```

### 原因
mem0 默认使用 OpenAI 的 `text-embedding-ada-002` 嵌入模型,但你的 API 提供商不支持该模型。

### 解决方案

#### 步骤 1: 配置正确的嵌入模型

在 `.env` 文件中添加 `EMBEDDING_MODEL` 配置:

**SiliconFlow 用户:**
```bash
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

**DeepSeek 用户:**
```bash
# DeepSeek 暂不支持嵌入模型,建议使用其他提供商
```

**OpenAI 用户:**
```bash
EMBEDDING_MODEL=text-embedding-ada-002
```

**本地 Ollama 用户:**
```bash
# 需要先拉取嵌入模型
# ollama pull nomic-embed-text
EMBEDDING_MODEL=nomic-embed-text
```

#### 步骤 2: 清理旧数据

```bash
# 删除旧的记忆数据库
rm -rf data/qdrant

# 或完全清理 data 目录
rm -rf data
```

#### 步骤 3: 重启应用

```bash
uv run youyou
```

---

## 问题 2: API 密钥错误

### 症状
```
配置验证失败,请检查 .env 文件
```

### 解决方案
检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确填写。

---

## 问题 3: 记忆功能无响应

### 症状
记录物品后没有反馈,或查询时返回空结果。

### 解决方案

1. **检查记忆系统初始化:**
   启动时应该看到:
   ```
   记忆系统初始化成功: data/qdrant
   ```

2. **检查 data 目录权限:**
   ```bash
   ls -la data/
   # 确保有读写权限
   ```

3. **查看详细错误:**
   在代码中临时启用调试:
   ```python
   # 在 memory.py 中
   except Exception as e:
       print(f"详细错误: {e}")
       import traceback
       traceback.print_exc()
   ```

---

## 问题 4: LangChain 导入错误

### 症状
```
ImportError: cannot import name 'create_agent' from 'langchain.agents'
```

### 解决方案
确保安装了正确版本的 LangChain:
```bash
uv sync
```

---

## 常见 API 提供商配置

### SiliconFlow
```bash
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_API_KEY=sk-xxxxx
ROUTER_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
AGENT_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

### DeepSeek
```bash
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=sk-xxxxx
ROUTER_MODEL=deepseek-chat
AGENT_MODEL=deepseek-chat
# DeepSeek 暂不支持嵌入,需使用其他服务
```

### OpenAI
```bash
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxxxx
ROUTER_MODEL=gpt-3.5-turbo
AGENT_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-ada-002
```

### Ollama (本地)
```bash
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
ROUTER_MODEL=llama2
AGENT_MODEL=llama2
EMBEDDING_MODEL=nomic-embed-text
```

---

## 调试技巧

### 1. 查看当前配置
运行 YouYou 后输入:
```
/config
```

### 2. 测试 API 连接
```bash
curl -X POST "${OPENAI_API_BASE}/chat/completions" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "你的模型名称",
    "messages": [{"role": "user", "content": "测试"}]
  }'
```

### 3. 查看日志
启用 Python 详细输出:
```bash
uv run python -u -m youyou.cli
```

---

## 获取帮助

如果问题仍未解决:

1. 检查你的 API 提供商文档,确认支持的模型列表
2. 查看 mem0 文档: https://docs.mem0.ai/
3. 查看 LangChain 文档: https://python.langchain.com/

