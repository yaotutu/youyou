# YouYou 客户端-服务端使用指南

## 架构说明

YouYou 现在采用客户端-服务端分离架构:

```
┌──────────────┐                    ┌──────────────┐
│              │   HTTP (JSON)      │              │
│   CLI 客户端  │ ◄─────────────────► │   服务端      │
│              │   localhost:8000   │  (Flask)     │
└──────────────┘                    └──────────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │  Supervisor  │
                                    │    Agent     │
                                    └──────────────┘
                                            │
                                    ┌───────┴───────┐
                                    ▼               ▼
                            ┌───────────┐   ┌───────────┐
                            │Item Agent │   │Chat Agent │
                            └───────────┘   └───────────┘
```

## 快速开始

### 准备工作

1. **确保已配置 .env 文件**
   ```bash
   # 检查配置
   cat .env
   ```

2. **清理旧数据** (如果遇到过嵌入模型错误)
   ```bash
   rm -rf data/qdrant
   ```

### 启动方式

**推荐: 使用两个终端窗口**

#### 终端 1 - 启动服务端
```bash
cd /Users/yaotutu/Desktop/code/youyou
uv run youyou-server
```

你会看到:
```
============================================================
YouYou 服务启动中...
============================================================
API Base: https://api.siliconflow.cn/v1
Router Model: Pro/deepseek-ai/DeepSeek-V3.1-Terminus
Agent Model: Pro/deepseek-ai/DeepSeek-V3.1-Terminus
Embedding Model: BAAI/bge-large-zh-v1.5
Data Directory: ./data
============================================================
服务运行在: http://127.0.0.1:8000
按 Ctrl+C 停止服务
============================================================
```

**保持这个终端打开,你可以实时观察日志!**

#### 终端 2 - 启动客户端
```bash
cd /Users/yaotutu/Desktop/code/youyou
uv run youyou
```

## 使用示例

### 服务端日志示例

```
2025-01-05 10:30:15 [INFO] 收到用户消息: 钥匙在门口抽屉里
2025-01-05 10:30:16 [INFO] 记忆系统初始化成功: data/qdrant
2025-01-05 10:30:18 [INFO] 返回响应: 好的,我已经记住了,钥匙在门口抽屉里
2025-01-05 10:30:20 [INFO] 收到用户消息: 钥匙在哪?
2025-01-05 10:30:21 [INFO] 返回响应: 钥匙在门口抽屉里
```

### 客户端交互示例

```
# YouYou 助手 (客户端)

你的本地智能助理,支持:
- 对话交流
- 物品位置记忆

✓ 已连接到服务端 (http://127.0.0.1:8000)

你: 钥匙在门口抽屉里
YouYou: 好的,我已经记住了,钥匙在门口抽屉里

你: 钥匙在哪?
YouYou: 钥匙在门口抽屉里
```

## 客户端命令

| 命令 | 功能 |
|------|------|
| `/status` | 检查服务端状态 |
| `/config` | 查看服务端配置 |
| `/help` | 显示帮助信息 |
| `/clear` | 清空屏幕 |
| `/exit` 或 `/quit` | 退出客户端 |

## API 端点

服务端提供 RESTful API,可以用于集成其他客户端:

### 健康检查
```bash
curl http://127.0.0.1:8000/health
```

响应:
```json
{
  "status": "ok",
  "timestamp": "2025-01-05T10:30:00.123456"
}
```

### 获取配置
```bash
curl http://127.0.0.1:8000/config
```

响应:
```json
{
  "api_base": "https://api.siliconflow.cn/v1",
  "api_key": "**********hgk",
  "router_model": "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
  "agent_model": "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
  "embedding_model": "BAAI/bge-large-zh-v1.5",
  "user_id": "default",
  "data_dir": "./data"
}
```

### 发送消息
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

响应:
```json
{
  "response": "你好!我是 YouYou,你的个人助理。",
  "timestamp": "2025-01-05T10:30:00.123456"
}
```

## 故障排查

### 问题 1: 客户端无法连接服务端

**症状:**
```
✗ 无法连接到服务端 (http://127.0.0.1:8000)
```

**解决方案:**
1. 确保服务端已启动: `uv run youyou-server`
2. 检查端口 8000 是否被占用: `lsof -i :8000`
3. 如果端口被占用,可以修改 `server.py` 中的 `port` 变量

### 问题 2: 服务端启动失败

**症状:**
```
配置验证失败,请检查 .env 文件
```

**解决方案:**
检查 .env 文件是否正确配置:
- `OPENAI_API_KEY` 不为空
- `OPENAI_API_BASE` 正确
- `EMBEDDING_MODEL` 已配置

### 问题 3: 记忆功能报错

**症状:**
```
搜索失败: Error code: 400 - Model does not exist
```

**解决方案:**
1. 清理旧数据: `rm -rf data/qdrant`
2. 确保 `.env` 中配置了正确的 `EMBEDDING_MODEL`
3. 重启服务端

## 优势

### 1. 清晰的日志输出
服务端终端可以看到所有请求和响应的详细日志,方便调试和监控。

### 2. 客户端可以随时重启
客户端崩溃或需要重启时,不影响服务端,对话状态保持。

### 3. 支持多客户端
可以同时启动多个客户端连接到同一个服务端。

### 4. 易于扩展
- 可以添加 Web UI 客户端
- 可以添加移动端客户端
- 可以集成到其他应用中

## 开发建议

### 调试模式
在 `server.py` 中启用 Flask 调试模式:
```python
app.run(host=host, port=port, debug=True)
```

### 自定义端口
修改 `server.py` 中的端口:
```python
port = 9000  # 改为你想要的端口
```

同时修改 `cli.py` 中的服务端地址:
```python
SERVER_URL = "http://127.0.0.1:9000"
```

### 日志级别
在 `server.py` 中调整日志级别:
```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 查看更详细日志
    ...
)
```

---

享受 YouYou 助手的新架构! 🎉
