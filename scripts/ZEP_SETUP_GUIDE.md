# Zep 记忆系统集成指南

## 📋 概述

YouYou 现已集成 Zep 作为全局记忆中枢，提供：
- ✅ 跨轮对话上下文理解
- ✅ 语义搜索历史对话
- ✅ ItemAgent 查询兜底
- ✅ 自动事实提取和摘要

## 🚀 快速开始

### 方案 A: 使用 Zep Cloud（推荐新手）

1. **注册 Zep Cloud 账号**
   - 访问: https://www.getzep.com/
   - 注册并获取 API Key
   - 免费层支持 1000 条消息/月

2. **配置环境变量**
   ```bash
   # 编辑 .env 文件
   ZEP_API_KEY=your_zep_cloud_api_key_here
   ```

3. **安装依赖**
   ```bash
   uv sync
   ```

4. **启动服务**
   ```bash
   uv run youyou-server
   ```

### 方案 B: 本地部署 Zep（推荐进阶用户）

1. **使用 Docker 启动 Zep**
   ```bash
   # 拉取最新镜像
   docker pull ghcr.io/getzep/zep:latest

   # 启动 Zep 服务
   docker run -d \
     --name zep \
     -p 8000:8000 \
     -e ZEP_AUTH_REQUIRED=false \
     ghcr.io/getzep/zep:latest
   ```

2. **配置环境变量**
   ```bash
   # 编辑 .env 文件
   # 不设置 ZEP_API_KEY，默认使用本地部署
   ZEP_API_URL=http://localhost:8000
   ```

3. **安装依赖**
   ```bash
   uv sync
   ```

4. **启动服务**
   ```bash
   uv run youyou-server
   ```

## 🧪 测试集成

运行测试脚本验证 Zep 集成是否正常：

```bash
uv run python scripts/test_zep_integration.py
```

测试内容：
- ✅ Zep 基础功能（记录、查询、搜索）
- ✅ 跨轮对话引用理解
- ✅ ItemAgent 五级查询兜底
- ✅ 上下文感知能力

## 📊 架构说明

### 三层记忆架构

```
┌──────────────────────────────────────────┐
│         Zep Memory (顶层)                │
│   - 所有对话历史                          │
│   - 语义搜索能力                          │
│   - 自动摘要和事实提取                     │
└──────────────────────────────────────────┘
          ↑                ↑
     记录所有交互        提供上下文
          │                │
┌─────────────────────────────────────────┐
│         Supervisor Agent                │
│   - 携带 Zep 上下文进行路由              │
└─────────────────────────────────────────┘
          ↓              ↓
    ┌─────────┐    ┌──────────┐
    │ItemAgent│    │ChatAgent │
    └─────────┘    └──────────┘
          ↓
    ┌─────────┐
    │ SQLite  │    (结构化存储)
    └─────────┘
          ↓
      失败 → Zep 兜底
```

### 五级查询策略（ItemAgent）

1. **精确匹配** (SQLite)
2. **别名匹配** (SQLite)
3. **全文搜索** (SQLite FTS5)
4. **关键词模糊** (SQLite LIKE)
5. **语义搜索** (Zep 兜底) ⭐ 新增

## 💡 使用场景

### 场景 1: 代词引用理解

```
用户: 钥匙在桌子上
系统: ✓ 已记住：钥匙在桌子上

用户: 它在哪？
系统: ✓ 钥匙在桌子上（理解"它"指钥匙）
```

### 场景 2: 非结构化物品提及

```
用户: 我把临时门禁卡放车里了
系统: 知道了

（3天后）
用户: 临时门禁卡在哪？
系统: ✓ 在车里（Zep 兜底找到历史对话）
```

### 场景 3: 上下文推理

```
用户: 我准备去健身房
系统: 好的

用户: 运动耳机在哪？
系统: ✓ 运动耳机在储物柜（结合上下文理解需求）
```

## 🔧 配置选项

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ZEP_API_KEY` | Zep Cloud API Key（可选） | 空 |
| `ZEP_API_URL` | 本地 Zep URL（可选） | `http://localhost:8000` |

### 上下文窗口

在 `server.py` 中可以调整上下文窗口大小：

```python
# 获取最近 N 条对话
recent_context = zep.get_recent_context(limit=10)  # 默认 10 条
```

## 🐛 故障排查

### 问题 1: Zep 初始化失败

**症状**: 启动时显示 "Zep 初始化失败"

**解决方案**:
1. 检查 Zep 服务是否运行：
   ```bash
   curl http://localhost:8000/healthz  # 本地部署
   ```
2. 检查 API Key 是否正确（Cloud）
3. 查看详细错误日志

**注意**: Zep 初始化失败不会影响系统运行，只是无记忆模式。

### 问题 2: 搜索结果为空

**症状**: Zep 搜索总是返回空结果

**可能原因**:
1. Zep session 中没有足够的消息（需要至少 2-3 条对话）
2. 搜索查询太模糊
3. Zep 嵌入模型尚未索引消息（稍等片刻）

**解决方案**:
```bash
# 运行测试脚本添加测试数据
uv run python scripts/test_zep_integration.py
```

### 问题 3: Docker 端口冲突

**症状**: `docker run` 报错端口 8000 已被占用

**解决方案**:
```bash
# 使用其他端口
docker run -d --name zep -p 8080:8000 ghcr.io/getzep/zep:latest

# 更新 .env
ZEP_API_URL=http://localhost:8080
```

## 📚 更多资源

- [Zep 官方文档](https://docs.getzep.com/)
- [Zep GitHub](https://github.com/getzep/zep)
- [Zep Cloud 控制台](https://app.getzep.com/)

## 🔄 升级和维护

### 更新 Zep 依赖

```bash
# 更新到最新版本
uv sync --upgrade-package zep-cloud
uv sync --upgrade-package zep-python
```

### 清理 Zep 数据

```bash
# 方案 A: Zep Cloud - 在控制台删除 session
# 访问: https://app.getzep.com/

# 方案 B: 本地部署 - 重启容器
docker rm -f zep
docker run -d --name zep -p 8000:8000 ghcr.io/getzep/zep:latest
```

## ✅ 验证清单

- [ ] Zep 服务正常运行（Cloud 或本地）
- [ ] 环境变量配置正确
- [ ] 依赖已安装（`uv sync`）
- [ ] 测试脚本通过（`test_zep_integration.py`）
- [ ] 能够正常对话并保存到 Zep
- [ ] 跨轮对话引用正常工作

---

**🎉 恭喜！Zep 集成完成，享受增强的记忆能力吧！**
