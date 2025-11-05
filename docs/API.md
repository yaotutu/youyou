# YouYou API 文档

YouYou 提供标准的 RESTful API 接口，支持 OpenAPI/Swagger 规范。

## API 基础信息

- **基础地址**: `http://127.0.0.1:8000/api/v1`
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **OpenAPI Spec**: `http://127.0.0.1:8000/swagger.json`

## 接口列表

### 1. 对话接口

#### POST /api/v1/chat/message

发送消息给助手。

**请求体**:
```json
{
  "message": "钥匙放在书桌抽屉里"
}
```

**响应**:
```json
{
  "response": "好的，我已经记录了：钥匙放在书桌抽屉里。",
  "timestamp": "2025-11-05T12:00:00"
}
```

**支持的功能**:
- 记录物品位置：如 "钥匙放在书桌抽屉里"
- 查询物品位置：如 "钥匙在哪？"
- 列出所有物品：如 "我记录了哪些物品？"
- 日常对话：如 "你好"、"今天天气怎么样"

**示例**:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "钥匙放在书桌抽屉里"}'
```

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/v1/chat/message",
    json={"message": "钥匙放在书桌抽屉里"}
)
print(response.json())
```

### 2. 系统接口

#### GET /api/v1/system/health

健康检查接口。

**响应**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-05T12:00:00"
}
```

**示例**:
```bash
curl http://127.0.0.1:8000/api/v1/system/health
```

#### GET /api/v1/system/config

获取系统配置信息。

**响应**:
```json
{
  "api_base": "https://api.siliconflow.cn/v1",
  "api_key": "**********hgk",
  "router_model": "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
  "agent_model": "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
  "embedding_model": "Qwen/Qwen3-Embedding-8B",
  "user_id": "default",
  "data_dir": "data"
}
```

**示例**:
```bash
curl http://127.0.0.1:8000/api/v1/system/config
```

## 使用 Swagger UI

1. 启动服务后，访问 http://127.0.0.1:8000/docs
2. 在 Swagger UI 中可以：
   - 查看所有可用接口
   - 查看请求/响应模型
   - 直接测试 API
   - 下载 OpenAPI 规范

## 错误处理

所有接口在出错时返回统一的错误格式：

```json
{
  "error": "错误信息描述"
}
```

常见 HTTP 状态码：
- `200` - 成功
- `400` - 请求参数错误
- `500` - 服务器内部错误

## CORS 支持

API 已启用 CORS，支持跨域请求。
