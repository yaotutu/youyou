# YouYou 测试指南

本目录包含 YouYou 项目的综合测试脚本和文档。

## 文件说明

### 测试脚本

- **`test_business_logic.py`** - 综合业务逻辑测试脚本
  - 覆盖所有核心功能
  - 自动化测试流程
  - 详细的测试报告

### 文档

- **`BUSINESS_LOGIC_ANALYSIS.md`** - 业务逻辑全面分析文档
  - 系统架构详解
  - 核心流程分析
  - 数据流图示
  - 关键组件说明

- **`TEST_REPORT_TEMPLATE.md`** - 测试报告模板
  - 标准化测试报告格式
  - 详细的测试项说明
  - 数据一致性验证

- **`TEST_README.md`** - 本文件
  - 测试使用说明
  - 快速开始指南

---

## 快速开始

### 1. 前置条件

确保已完成以下准备:

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量 (.env 文件)
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_API_KEY=your_api_key_here
ROUTER_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
AGENT_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
USER_ID=default
DATA_DIR=./data

# 3. (可选) 配置 Zep 记忆系统
ZEP_API_KEY=your_zep_api_key  # 如果使用 Zep Cloud
ZEP_API_URL=http://localhost:8000  # 如果使用本地 Zep
```

### 2. 启动服务端

在一个终端窗口中启动 YouYou 服务端:

```bash
uv run youyou-server
```

等待服务启动完成,看到以下输出:

```
============================================================
YouYou API 服务启动中...
============================================================
API Base: https://api.siliconflow.cn/v1
Router Model: Pro/deepseek-ai/DeepSeek-V3.1-Terminus
Agent Model: Pro/deepseek-ai/DeepSeek-V3.1-Terminus
Data Directory: ./data
============================================================
API 服务运行在: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs
按 Ctrl+C 停止服务
============================================================
```

### 3. 运行测试

在另一个终端窗口中运行测试脚本:

```bash
uv run python scripts/test_business_logic.py
```

---

## 测试内容

测试脚本会自动执行以下测试:

### 1. 基础功能测试 (2 项)
- 健康检查端点
- 配置端点

### 2. 物品记录测试 (4 项)
- 记录单个物品
- 重复记录相同位置
- 更新物品位置
- 复杂物品名称

### 3. 物品查询测试 - 五级策略 (5 项)
- Level 1: 精确匹配查询
- Level 2: 别名匹配查询
- Level 3: 全文搜索查询
- Level 4: 关键词模糊匹配
- 查询不存在的物品

### 4. 列出物品测试 (1 项)
- 列出所有物品

### 5. Supervisor 路由测试 (2 项)
- 路由到 ItemAgent
- 路由到 ChatAgent

### 6. ChatAgent 对话测试 (2 项)
- 简单问候
- 一般性问题

### 7. 会话历史和上下文测试 (2 项)
- 代词引用测试
- 多轮对话测试

### 8. 边界情况测试 (3 项)
- 空消息处理
- 超长消息处理
- 特殊字符处理

### 9. Zep 记忆兜底测试 (1 项)
- Zep 语义搜索

### 10. 性能测试 (2 项)
- 并发请求处理
- 响应时间测试

**总计**: 约 24 项测试

---

## 测试输出示例

### 成功运行的输出

```
================================================================================
YouYou 业务逻辑综合测试
================================================================================

ℹ 检查服务器状态...
✓ 服务器正常运行

--------------------------------------------------------------------------------
1. 基础功能测试
--------------------------------------------------------------------------------

[测试] 健康检查端点
✓ 通过 (0.05s)

[测试] 配置端点
ℹ   API Base: https://api.siliconflow.cn/v1
ℹ   Router Model: Pro/deepseek-ai/DeepSeek-V3.1-Terminus
✓ 通过 (0.03s)

--------------------------------------------------------------------------------
2. 物品记录测试
--------------------------------------------------------------------------------

[测试] 记录单个物品
ℹ   响应: 已记住: 测试钥匙在测试桌子上
✓ 通过 (2.15s)

[测试] 重复记录相同位置
ℹ   响应: 测试手机确实在测试背包
✓ 通过 (1.87s)

[测试] 更新物品位置
ℹ   响应: 测试笔记本已从测试客厅移动到测试卧室
✓ 通过 (2.34s)

[测试] 复杂物品名称
ℹ   测试了 3 个复杂物品名称
✓ 通过 (5.12s)

...

================================================================================
测试套件: YouYou 业务逻辑综合测试 - 测试摘要
================================================================================
总测试数: 24
通过: 22
失败: 2
总耗时: 45.67s
通过率: 91.7%

失败的测试:
  ✗ 代词引用测试
    错误: 上下文测试失败
  ✗ Zep 语义搜索
    错误: Zep 兜底测试失败
```

### 测试失败的常见原因

1. **服务器未启动**
   ```
   ✗ 无法连接到服务器,请确保 youyou-server 已启动
   ```
   解决方案: 先运行 `uv run youyou-server`

2. **API Key 未配置**
   ```
   ✗ HTTP 500: API Key 错误
   ```
   解决方案: 检查 `.env` 文件中的 `OPENAI_API_KEY`

3. **Zep 未配置**
   ```
   ⚠ 注意: Zep 兜底功能依赖于 Zep 配置
   ```
   说明: Zep 记忆测试需要配置 Zep 服务,可选功能

4. **网络超时**
   ```
   ✗ 请求超时 (>30秒)
   ```
   解决方案: 检查网络连接,或增加超时时间

---

## 高级用法

### 自定义测试配置

编辑 `test_business_logic.py` 文件顶部的配置:

```python
API_BASE_URL = "http://127.0.0.1:8000"  # 修改服务地址
TEST_TIMEOUT = 30  # 修改超时时间(秒)
```

### 运行单个测试

如果只想测试特定功能,可以修改 `run_all_tests()` 方法:

```python
def run_all_tests(self):
    self.suite.start()

    # 只运行基础功能测试
    print_section("1. 基础功能测试")
    self._test_health_check()
    self._test_config_endpoint()

    # 注释掉其他测试...

    self.suite.end()
    self.suite.print_summary()
```

### 增加测试用例

在 `BusinessLogicTests` 类中添加新的测试方法:

```python
def _test_my_new_feature(self):
    """测试我的新功能"""
    def test(result: TestResult):
        # 编写测试逻辑
        success, response, error = self.client.send_message("测试消息")

        # 验证结果
        result.passed = success and "预期内容" in response.get("response", "")

        if not result.passed:
            result.error_message = error or "测试失败原因"

    self._run_test("我的新功能", test)
```

然后在 `run_all_tests()` 中调用:

```python
print_section("11. 自定义测试")
self._test_my_new_feature()
```

---

## 调试测试

### 查看详细日志

服务端会输出详细的日志信息,包括:
- Agent 调用过程
- 数据库查询策略
- Zep 记忆操作
- 错误堆栈信息

### 检查数据库状态

测试后可以检查数据库内容:

```bash
# 查看所有物品
sqlite3 data/items.db "SELECT * FROM items;"

# 查看历史记录
sqlite3 data/items.db "SELECT * FROM item_history ORDER BY timestamp DESC LIMIT 10;"

# 查看 FTS5 索引
sqlite3 data/items.db "SELECT * FROM items_fts;"
```

### 清理测试数据

如果需要清理测试数据:

```bash
# 删除数据库文件
rm data/items.db

# 或者删除整个数据目录
rm -rf data/

# 服务会自动重新创建空数据库
```

---

## 持续集成 (CI)

### GitHub Actions 示例

创建 `.github/workflows/test.yml`:

```yaml
name: YouYou Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: uv sync

    - name: Setup environment
      run: |
        echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
        echo "OPENAI_API_BASE=https://api.siliconflow.cn/v1" >> .env
        # ... 其他配置 ...

    - name: Start server
      run: uv run youyou-server &
      env:
        PYTHONUNBUFFERED: 1

    - name: Wait for server
      run: |
        timeout 30 bash -c 'until curl -f http://127.0.0.1:8000/api/v1/system/health; do sleep 1; done'

    - name: Run tests
      run: uv run python scripts/test_business_logic.py
```

---

## 性能基准

### 响应时间参考 (基于 DeepSeek V3.1)

| 操作类型 | 平均响应时间 | 说明 |
|---------|-------------|------|
| 记录物品 | 1.5 - 2.5s | LLM 参数提取 + 数据库写入 |
| 查询物品 (精确) | 0.8 - 1.5s | 主要是 LLM 推理 |
| 查询物品 (模糊) | 1.5 - 3.0s | 多级查询策略 |
| 列出物品 | 1.0 - 2.0s | 数据库查询 + LLM 格式化 |
| 一般对话 | 1.5 - 3.0s | LLM 推理 |
| 上下文对话 | 2.0 - 4.0s | 加载历史 + LLM 推理 |

### 并发性能

- **5 并发**: 平均 2-3s/请求
- **10 并发**: 平均 3-5s/请求
- **瓶颈**: LLM API 调用

---

## 故障排查

### 常见问题

#### 1. 测试一直卡住不动

**可能原因**: LLM API 超时

**解决方案**:
- 检查网络连接
- 验证 API Key 是否有效
- 检查 API Base URL 是否正确
- 增加 `TEST_TIMEOUT` 配置

#### 2. 部分测试失败

**可能原因**:
- 模型响应不稳定
- 上下文理解失败

**解决方案**:
- 多次运行测试(某些测试依赖 LLM 理解能力)
- 检查提示词是否清晰
- 调整 temperature 参数

#### 3. 数据库锁定错误

**错误**: `database is locked`

**解决方案**:
```bash
# 确保没有其他进程占用数据库
lsof data/items.db

# 删除 WAL 文件
rm data/items.db-wal data/items.db-shm

# 重启服务
```

#### 4. Zep 相关测试全部失败

**可能原因**: Zep 未配置或服务不可用

**解决方案**:
- 这是正常现象,Zep 是可选功能
- 如需使用 Zep,参考 `scripts/ZEP_SETUP_GUIDE.md`

---

## 参考资源

- **项目文档**: `/Users/yaotutu/Desktop/code/youyou/CLAUDE.md`
- **业务逻辑分析**: `scripts/BUSINESS_LOGIC_ANALYSIS.md`
- **测试报告模板**: `scripts/TEST_REPORT_TEMPLATE.md`
- **Zep 设置指南**: `scripts/ZEP_SETUP_GUIDE.md`

---

## 贡献指南

如果你想添加新的测试用例:

1. 在 `test_business_logic.py` 中添加测试方法
2. 遵循现有的测试模式
3. 添加清晰的注释说明测试目的
4. 更新本文档的测试列表
5. 提交 Pull Request

---

**最后更新**: 2025-11-06
**维护者**: Claude Code
**版本**: v1.0
