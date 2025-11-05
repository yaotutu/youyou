# YouYou API 使用示例

## 启动服务

```bash
uv run youyou-server
```

服务启动后会显示：
```
YouYou API 服务启动中...
API 服务运行在: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs
OpenAPI Spec: http://127.0.0.1:8000/swagger.json
```

## 使用 Swagger UI（推荐）

1. 打开浏览器访问：http://127.0.0.1:8000/docs

2. 在 Swagger UI 中：
   - 展开 `POST /api/v1/chat/message` 接口
   - 点击 "Try it out"
   - 输入消息，例如：`"钥匙放在书桌抽屉里"`
   - 点击 "Execute"
   - 查看响应结果

## 使用 curl

### 记录物品位置

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "钥匙放在书桌抽屉里"}'
```

响应：
```json
{
  "response": "好的，我已经记录了：钥匙放在书桌抽屉里。",
  "timestamp": "2025-11-05T12:00:00"
}
```

### 查询物品位置

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "钥匙在哪？"}'
```

响应：
```json
{
  "response": "钥匙在书桌抽屉里。",
  "timestamp": "2025-11-05T12:00:00"
}
```

### 列出所有物品

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "我记录了哪些物品？"}'
```

### 日常对话

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

## 使用 Python

```python
import requests

# API 基础地址
BASE_URL = "http://127.0.0.1:8000/api/v1"

# 发送消息
def send_message(message: str):
    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={"message": message}
    )
    return response.json()

# 记录物品
result = send_message("钥匙放在书桌抽屉里")
print(result['response'])
# 输出: 好的，我已经记录了：钥匙放在书桌抽屉里。

# 查询物品
result = send_message("钥匙在哪？")
print(result['response'])
# 输出: 钥匙在书桌抽屉里。

# 列出所有物品
result = send_message("我记录了哪些物品？")
print(result['response'])
```

## 使用 JavaScript/TypeScript

```javascript
// 使用 fetch API
async function sendMessage(message) {
    const response = await fetch('http://127.0.0.1:8000/api/v1/chat/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    });
    return await response.json();
}

// 记录物品
const result = await sendMessage('钥匙放在书桌抽屉里');
console.log(result.response);

// 查询物品
const result2 = await sendMessage('钥匙在哪？');
console.log(result2.response);
```

## 系统接口

### 健康检查

```bash
curl http://127.0.0.1:8000/api/v1/system/health
```

### 查看配置

```bash
curl http://127.0.0.1:8000/api/v1/system/config
```

## 错误处理

当请求失败时，API 会返回错误信息：

```json
{
  "error": "消息不能为空"
}
```

Python 示例：
```python
try:
    result = send_message("")
except requests.exceptions.HTTPError as e:
    print(f"错误: {e.response.json()['error']}")
```
