"""YouYou 服务端 - RESTful API with OpenAPI/Swagger"""
import logging
import socket
import subprocess
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any

from flask import Flask
from flask_restx import Api, Resource, fields
from flask_cors import CORS

from config import config
from agents.supervisor import supervisor
from agents.note_agent import note_agent
from agents.calendar_agent import calendar_agent
from core.zep_memory import get_zep_memory
from core.session_history import get_session_manager
from core.tag_parser import TagParser
from core.keyword_router import KeywordRouter
from core.redirect_detector import detect_redirect
from core.interaction_logger import get_interaction_logger, InteractionLog
from core.response_types import AgentResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域

# 创建 API
api = Api(
    app,
    version='1.0',
    title='YouYou API',
    description='YouYou 本地智能助手 API - 支持物品位置记忆和智能对话',
    doc='/docs',  # Swagger UI 路径
    prefix='/api/v1'
)

# 创建命名空间
ns_chat = api.namespace('chat', description='对话相关接口')
ns_system = api.namespace('system', description='系统相关接口')

# 定义模型
chat_request_model = api.model('ChatRequest', {
    'message': fields.String(required=True, description='用户消息', example='钥匙放在书桌抽屉里')
})

# Action 模型 - 表示一个结构化操作
action_model = api.model('Action', {
    'type': fields.String(
        required=True,
        description='操作类型',
        enum=[
            'reminder_set',          # CalendarAgent: 提醒已设置
            'reminder_list',         # CalendarAgent: 提醒列表
            'reminder_deleted',      # CalendarAgent: 提醒已删除
            'note_saved',            # NoteAgent: 笔记已保存
            'note_search_results',   # NoteAgent: 笔记搜索结果
            'item_remembered',       # ItemAgent: 物品位置已记录
            'item_location',         # ItemAgent: 物品位置查询结果
            'item_list',             # ItemAgent: 物品列表
            'chat_response',         # Supervisor/ChatAgent: 普通对话
            'error',                 # 通用: 错误
        ],
        example='reminder_set'
    ),
    'data': fields.Raw(
        required=True,
        description='''操作相关的结构化数据，根据 type 不同而不同:

reminder_set (提醒已设置):
{
  "title": "开会",
  "time": "2025-11-08T15:00:00",
  "reminder_minutes": 15,
  "duration_minutes": 60,
  "reminder_id": "rem_xxx"
}

reminder_list (提醒列表):
{
  "reminders": [
    {
      "id": "rem_xxx",
      "title": "开会",
      "time": "2025-11-08T15:00:00",
      "reminder_minutes": 15,
      "duration_minutes": 60
    }
  ],
  "count": 1
}

reminder_deleted (提醒已删除):
{
  "reminder_id": "rem_xxx",
  "title": "开会"
}

note_saved (笔记已保存):
{
  "note_id": "note_xxx",
  "content": "完整测试流程记录",
  "tags": ["测试", "流程"],
  "github_url": "https://...",
  "github_metadata": {...}
}

note_search_results (笔记搜索结果):
{
  "results": [
    {
      "note_id": "note_xxx",
      "content": "...",
      "tags": [...],
      "relevance_score": 0.95
    }
  ],
  "count": 5
}

item_remembered (物品位置已记录):
{
  "item": "钥匙",
  "location": "书桌抽屉"
}

item_location (物品位置查询结果):
{
  "item": "钥匙",
  "location": "书桌抽屉",
  "confidence": 0.95
}

item_list (物品列表):
{
  "items": [
    {
      "item": "钥匙",
      "location": "书桌抽屉"
    }
  ],
  "count": 3
}

chat_response (普通对话):
{
  "text": "你好！我是YouYou..."
}

error (错误):
{
  "error_type": "validation_error",
  "details": "..."
}
''',
        example={
            "title": "开会",
            "time": "2025-11-08T15:00:00",
            "reminder_minutes": 15,
            "duration_minutes": 60,
            "reminder_id": "rem_abc123"
        }
    )
})

# AgentResponse 模型 - 统一的 API 响应格式
agent_response_model = api.model('AgentResponse', {
    'success': fields.Boolean(
        required=True,
        description='操作是否成功',
        example=True
    ),
    'agent': fields.String(
        required=True,
        description='处理此请求的 Agent 名称',
        enum=['supervisor', 'note_agent', 'calendar_agent', 'item_agent', 'chat_agent'],
        example='calendar_agent'
    ),
    'message': fields.String(
        required=True,
        description='人类可读的消息文本，适合直接展示给用户',
        example='好的，我已经为你设置了明天下午3点的开会提醒，会提前15分钟通知你。'
    ),
    'actions': fields.List(
        fields.Nested(action_model),
        required=True,
        description='操作列表，一次请求可能触发多个操作（如设置提醒同时返回提醒列表）',
        example=[{
            "type": "reminder_set",
            "data": {
                "title": "开会",
                "time": "2025-11-08T15:00:00",
                "reminder_minutes": 15,
                "duration_minutes": 60,
                "reminder_id": "rem_abc123"
            }
        }]
    ),
    'timestamp': fields.String(
        required=True,
        description='响应时间戳 (ISO 8601 格式)',
        example='2025-11-07T14:30:00.123456'
    ),
    'error': fields.String(
        required=False,
        description='错误信息（仅当 success=false 时存在）',
        example='无法解析时间格式'
    )
})

error_model = api.model('Error', {
    'error': fields.String(description='错误信息')
})

config_model = api.model('Config', {
    'api_base': fields.String(description='API 基础地址'),
    'api_key': fields.String(description='API 密钥（部分隐藏）'),
    'router_model': fields.String(description='路由模型'),
    'agent_model': fields.String(description='Agent 模型'),
    'embedding_model': fields.String(description='嵌入模型'),
    'user_id': fields.String(description='用户 ID'),
    'data_dir': fields.String(description='数据目录')
})

health_model = api.model('Health', {
    'status': fields.String(description='服务状态', example='ok'),
    'timestamp': fields.String(description='时间戳')
})


def _log_interaction(user_input: str, response: str, start_time: float, log_data: dict):
    """记录交互日志的辅助函数"""
    try:
        response_time_ms = int((time.time() - start_time) * 1000)

        log_entry = InteractionLog(
            user_id=config.USER_ID,
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            input_length=len(user_input),
            response_text=response,
            response_length=len(response) if response else 0,
            response_time_ms=response_time_ms,
            routing_stage=log_data.get('routing_stage', 'unknown'),
            routing_matched=log_data.get('routing_matched', False),
            routing_keywords=log_data.get('routing_keywords'),
            target_agent=log_data.get('target_agent'),
            redirect_occurred=log_data.get('redirect_occurred', False),
            redirect_reason=log_data.get('redirect_reason'),
            final_agent=log_data.get('final_agent'),
            status=log_data.get('status', 'success')
        )

        get_interaction_logger().log(log_entry)
    except Exception as e:
        logger.error(f"[交互日志] 记录失败: {e}")


@ns_chat.route('/message')
class ChatMessage(Resource):
    """对话接口"""

    @ns_chat.doc('send_message')
    @ns_chat.expect(chat_request_model)
    @ns_chat.response(200, 'Success', agent_response_model)
    @ns_chat.response(400, 'Bad Request', error_model)
    @ns_chat.response(500, 'Internal Server Error', error_model)
    def post(self):
        """发送消息给助手

        支持的功能：
        - 设置日历提醒：如 "明天下午3点开会"、"11月20日下午2点面试"
        - 管理提醒：查看提醒列表、删除提醒
        - 保存笔记：如 "#note 记录一个想法" 或 "https://github.com/..."
        - 记录物品位置：如 "钥匙放在书桌抽屉里"
        - 查询物品位置：如 "钥匙在哪？"
        - 列出所有物品：如 "我记录了哪些物品？"
        - 日常对话：如 "你好"、"今天天气怎么样"

        返回格式：
        所有 Agent 返回统一的 AgentResponse 格式，包含：
        - success: 操作是否成功
        - agent: 处理此请求的 Agent 名称（supervisor/note_agent/calendar_agent/item_agent）
        - message: 人类可读的消息文本
        - actions: 结构化操作列表，每个操作包含 type 和 data
        - timestamp: 响应时间戳
        - error: 错误信息（仅失败时）

        actions 字段中的 type 可能包含：
        - reminder_set: 提醒已设置
        - reminder_list: 提醒列表
        - reminder_deleted: 提醒已删除
        - note_saved: 笔记已保存
        - note_search_results: 笔记搜索结果
        - item_remembered: 物品位置已记录
        - item_location: 物品位置查询结果
        - item_list: 物品列表
        - chat_response: 普通对话
        - error: 错误信息
        """
        # 开始计时和初始化日志数据
        start_time = time.time()
        log_data = {}

        try:
            data = api.payload
            user_input = data.get('message', '')

            if not user_input:
                return {"error": "消息不能为空"}, 400

            # 添加消息长度限制
            MAX_MESSAGE_LENGTH = 1000
            if len(user_input) > MAX_MESSAGE_LENGTH:
                logger.warning(f"消息过长: {len(user_input)} 字符 (最大 {MAX_MESSAGE_LENGTH})")
                return {"error": f"消息过长,最多支持 {MAX_MESSAGE_LENGTH} 个字符"}, 400

            logger.info("=" * 80)
            logger.info(f"📥 收到用户消息: {user_input}")
            logger.info("-" * 80)

            # 1. 解析标记，检测是否需要直接路由
            parse_result = TagParser.parse(user_input)

            if parse_result.has_tag:
                logger.info(f"🏷️  检测到标记: {parse_result.tag_type}")
                logger.info(f"🎯 目标 Agent: {parse_result.target_agent}")
                logger.info(f"📝 清理后的消息: {parse_result.clean_message}")

                # 记录标记路由信息
                log_data.update({
                    'routing_stage': 'tag',
                    'routing_matched': True,
                    'routing_keywords': json.dumps([f"标记:{parse_result.tag_type}"], ensure_ascii=False),
                    'target_agent': parse_result.target_agent,
                    'final_agent': parse_result.target_agent
                })

                # 直接路由到指定 Agent（跳过 Supervisor）
                if parse_result.target_agent == "note_agent":
                    logger.info("🚀 直接调用 NoteAgent (跳过 Supervisor)...")
                    agent_response = note_agent.invoke(parse_result.clean_message)
                    logger.info(f"📤 NoteAgent 返回响应 (前200字): {agent_response.message[:200]}...")

                    # 保存会话历史
                    session_mgr = get_session_manager(max_history_length=10, refresh_interval=0)
                    session_mgr.add_interaction(
                        user_id=config.USER_ID,
                        user_input=user_input,
                        assistant_response=agent_response.message,
                        agent_name="note_agent",
                        async_persist=True
                    )
                    logger.info("💾 交互已保存 (标记路由)")
                    logger.info("=" * 80)

                    # 记录交互日志
                    _log_interaction(user_input, agent_response.message, start_time, log_data)

                    # 返回完整的结构化响应
                    return agent_response.to_dict()

            # 2. 检查关键词路由（优先于 Supervisor）
            keyword_result = KeywordRouter.match(user_input)

            if keyword_result.matched:
                logger.info(f"🔑 检测到关键词路由")
                logger.info(f"🎯 目标 Agent: {keyword_result.target_agent}")
                logger.info(f"📌 匹配的关键词: {', '.join(keyword_result.matched_keywords)}")

                # 记录关键词路由信息
                log_data.update({
                    'routing_stage': 'keyword',
                    'routing_matched': True,
                    'routing_keywords': json.dumps(keyword_result.matched_keywords, ensure_ascii=False),
                    'target_agent': keyword_result.target_agent
                })

                # 直接路由到 calendar_agent
                if keyword_result.target_agent == "calendar_agent":
                    logger.info("🚀 直接调用 CalendarAgent (跳过 Supervisor)...")
                    agent_response = calendar_agent.invoke(keyword_result.original_message)
                    logger.info(f"📤 CalendarAgent 返回响应 (前200字): {agent_response.message[:200]}...")

                    # 检测是否需要回退 (检查 message 字段)
                    redirect_result = detect_redirect(agent_response.message)

                    if redirect_result.is_redirect:
                        logger.info(f"🔄 CalendarAgent 请求回退")
                        logger.info(f"📝 回退原因: {redirect_result.reason}")
                        logger.info("🔄 重新使用 Supervisor 路由...")

                        # 记录回退信息
                        log_data.update({
                            'redirect_occurred': True,
                            'redirect_reason': redirect_result.reason,
                            'final_agent': 'supervisor',
                            'status': 'redirect'
                        })

                        # 获取会话历史
                        session_mgr = get_session_manager(max_history_length=10, refresh_interval=0)
                        session_history = session_mgr.get_history(config.USER_ID)

                        # 构建带有回退提示的消息
                        enhanced_message = f"""[系统提示：calendar_agent 已判定此消息不属于日历范畴，原因：{redirect_result.reason}。请从其他可用工具中选择合适的 Agent 处理。]

{user_input}"""

                        messages = session_history + [
                            {"role": "user", "content": enhanced_message}
                        ]

                        # 调用 Supervisor 重新路由
                        result = supervisor.invoke({"messages": messages})

                        logger.info(f"✓ Supervisor 重新路由完成,消息数量: {len(result.get('messages', []))}")

                        # 提取响应
                        messages_list = result.get('messages', [])
                        final_message = messages_list[-1] if messages_list else None

                        if hasattr(final_message, 'content'):
                            response = final_message.content
                        else:
                            response = str(final_message)

                        logger.info(f"📤 Supervisor 返回响应 (前200字): {response[:200]}...")

                        # ⚠️ 保存到会话历史时使用原始消息（不包含系统提示）
                        session_mgr.add_interaction(
                            user_id=config.USER_ID,
                            user_input=user_input,  # 使用原始消息
                            assistant_response=response,
                            agent_name="supervisor",  # 标记为 supervisor 处理
                            async_persist=True
                        )
                        logger.info("💾 交互已保存 (回退路由)")
                        logger.info("=" * 80)

                        # 记录交互日志
                        _log_interaction(user_input, response, start_time, log_data)

                        # 构造统一的 AgentResponse 格式(回退到 Supervisor)
                        from core.response_types import Action
                        supervisor_response = AgentResponse(
                            success=True,
                            agent="supervisor",
                            message=response,
                            actions=[Action(type="chat_response", data={"text": response})]
                        )
                        return supervisor_response.to_dict()

                    # 没有回退，正常处理
                    log_data.update({'final_agent': 'calendar_agent'})

                    # 保存会话历史
                    session_mgr = get_session_manager(max_history_length=10, refresh_interval=0)
                    session_mgr.add_interaction(
                        user_id=config.USER_ID,
                        user_input=user_input,
                        assistant_response=agent_response.message,
                        agent_name="calendar_agent",
                        async_persist=True
                    )
                    logger.info("💾 交互已保存 (关键词路由)")
                    logger.info("=" * 80)

                    # 记录交互日志
                    _log_interaction(user_input, agent_response.message, start_time, log_data)

                    return agent_response.to_dict()

            # 3. 没有标记也没有关键词匹配，走正常的 Supervisor 路由
            logger.info("🔄 未检测到标记和关键词，使用 Supervisor 路由...")

            # 记录 Supervisor 路由信息
            log_data.update({
                'routing_stage': 'supervisor',
                'routing_matched': False,
                'target_agent': 'supervisor',
                'final_agent': 'supervisor'
            })

            # 获取会话历史管理器
            session_mgr = get_session_manager(max_history_length=10, refresh_interval=0)
            user_id = config.USER_ID

            # 从内存获取会话历史 (首次会从 Zep 加载)
            session_history = session_mgr.get_history(user_id)
            logger.info(f"📚 获取到 {len(session_history)} 条会话历史 (内存缓存)")

            # 构建完整的消息列表（会话历史 + 当前输入）
            messages = session_history + [{"role": "user", "content": user_input}]

            logger.info(f"📝 总消息数: {len(messages)} (历史 {len(session_history)} + 当前 1)")

            # 调用 supervisor 处理（现在有完整上下文）
            logger.info("🤖 调用 Supervisor Agent 处理请求...")
            result = supervisor.invoke({
                "messages": messages
            })

            logger.info(f"✓ Supervisor 返回结果,消息数量: {len(result.get('messages', []))}")

            # 打印所有消息用于调试
            messages_list = result.get('messages', [])
            for i, msg in enumerate(messages_list):
                msg_type = type(msg).__name__
                msg_content = getattr(msg, 'content', str(msg))[:100] if hasattr(msg, 'content') else str(msg)[:100]
                logger.info(f"  消息[{i}] {msg_type}: {msg_content}")

            # 提取响应 - 检查是否有 ToolMessage（子 agent 调用）
            from langchain_core.messages import ToolMessage
            from core.response_types import Action

            messages_result = result.get("messages", [])
            agent_data = None  # 用于存储从 ToolMessage 解析的数据
            response_text = ""
            actual_agent_name = "supervisor"  # 默认值

            # 查找 ToolMessage（说明 Supervisor 调用了子 agent）
            tool_message = None
            for msg in messages_result:
                if isinstance(msg, ToolMessage):
                    tool_message = msg
                    logger.info(f"🎯 找到 ToolMessage: {msg.content[:100]}...")
                    break

            if tool_message:
                # 透传模式：解析子 agent 返回的完整数据
                try:
                    agent_data = json.loads(tool_message.content)
                    actual_agent_name = agent_data.get("agent", "supervisor")
                    response_text = agent_data.get("message", "")
                    logger.info(f"✅ 透传子 agent 响应: agent={actual_agent_name}")
                    logger.info(f"📤 返回响应 (前200字): {response_text[:200]}...")
                except json.JSONDecodeError:
                    # 如果不是 JSON，回退到文本提取
                    response_text = tool_message.content
                    logger.warning("⚠️  ToolMessage.content 不是 JSON 格式，使用文本模式")
            else:
                # Supervisor 自处理模式：从 AIMessage 提取文本
                logger.info("💬 Supervisor 自处理对话（未调用子 agent）")
                for msg in reversed(messages_result):
                    content = getattr(msg, 'content', '')
                    if content and content.strip():
                        response_text = content
                        logger.info(f"从 {type(msg).__name__} 提取到响应: '{response_text[:100]}...'")
                        break

                if not response_text:
                    response_text = "抱歉,我无法处理这个请求"
                    logger.info("所有消息的 content 都为空")

            # 更新会话历史
            session_mgr.add_interaction(
                user_id=user_id,
                user_input=user_input,
                assistant_response=response_text,
                agent_name=actual_agent_name,  # 使用真实的 agent 名称
                async_persist=True
            )
            logger.info(f"💾 交互已保存: agent={actual_agent_name}")
            logger.info("=" * 80)

            # 记录交互日志
            _log_interaction(user_input, response_text, start_time, log_data)

            # 构造 AgentResponse
            if agent_data:
                # 透传模式：使用子 agent 返回的完整数据
                actions = [
                    Action(type=a["type"], data=a["data"])
                    for a in agent_data.get("actions", [])
                ]
                supervisor_response = AgentResponse(
                    success=agent_data.get("success", True),
                    agent=actual_agent_name,
                    message=response_text,
                    actions=actions
                )
            else:
                # Supervisor 自处理模式：构造简单响应
                supervisor_response = AgentResponse(
                    success=True,
                    agent="supervisor",
                    message=response_text,
                    actions=[Action(type="chat_response", data={"text": response_text})]
                )

            return supervisor_response.to_dict()

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ 处理请求时出错: {e}")
            logger.error("详细错误信息:", exc_info=True)
            logger.error("=" * 80)

            # 记录错误日志
            log_data.update({
                'status': 'error',
                'error_message': str(e)
            })
            error_response = f"处理请求时出错: {str(e)}"
            _log_interaction(user_input if 'user_input' in locals() else '', error_response, start_time, log_data)

            return {"error": str(e)}, 500


@ns_system.route('/health')
class Health(Resource):
    """健康检查"""

    @ns_system.doc('health_check')
    @ns_system.response(200, 'Success', health_model)
    def get(self):
        """检查服务健康状态"""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }


@ns_system.route('/config')
class Config(Resource):
    """配置信息"""

    @ns_system.doc('get_config')
    @ns_system.response(200, 'Success', config_model)
    def get(self):
        """获取当前系统配置"""
        masked_key = '*' * 10 + config.OPENAI_API_KEY[-4:] if config.OPENAI_API_KEY else '未设置'
        return {
            "api_base": config.OPENAI_API_BASE,
            "api_key": masked_key,
            "router_model": config.ROUTER_MODEL,
            "agent_model": config.AGENT_MODEL,
            "embedding_model": config.EMBEDDING_MODEL,
            "user_id": config.USER_ID,
            "data_dir": str(config.DATA_DIR)
        }


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def kill_process_on_port(port: int) -> bool:
    """杀掉占用指定端口的进程"""
    try:
        # macOS/Linux 使用 lsof 查找占用端口的进程
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    logger.info(f"🔪 发现占用端口 {port} 的进程 (PID: {pid}), 正在终止...")
                    subprocess.run(['kill', '-9', pid])
                    logger.info(f"✓ 已终止进程 {pid}")
            return True
        return False
    except FileNotFoundError:
        # lsof 命令不存在，可能在 Windows 上
        logger.warning("未找到 lsof 命令，无法自动清理端口")
        return False
    except Exception as e:
        logger.error(f"清理端口时出错: {e}")
        return False


def main():
    """启动服务"""
    if not config.validate():
        logger.error("配置验证失败,请检查 .env 文件")
        return

    # 启动 Flask 服务
    # 0.0.0.0 允许所有网络接口访问(包括局域网)
    host = "0.0.0.0"
    port = 8000

    # 检查端口占用
    if is_port_in_use(port):
        logger.warning(f"⚠️  端口 {port} 已被占用")
        if kill_process_on_port(port):
            logger.info("✓ 端口已清理，继续启动...")
            # 等待一小段时间确保端口释放
            import time
            time.sleep(0.5)
        else:
            logger.error(f"❌ 无法清理端口 {port}，请手动终止占用进程")
            logger.error(f"提示: 使用命令 'lsof -ti :{port}' 查找进程 PID")
            logger.error(f"      然后使用 'kill -9 <PID>' 终止进程")
            sys.exit(1)

    logger.info("=" * 60)
    logger.info("YouYou API 服务启动中...")
    logger.info("=" * 60)
    logger.info(f"API Base: {config.OPENAI_API_BASE}")
    logger.info(f"Router Model: {config.ROUTER_MODEL}")
    logger.info(f"Agent Model: {config.AGENT_MODEL}")
    logger.info(f"Embedding Model: {config.EMBEDDING_MODEL}")
    logger.info(f"Data Directory: {config.DATA_DIR}")
    logger.info("=" * 60)
    logger.info(f"API 服务运行在: http://{host}:{port}")
    logger.info(f"Swagger UI: http://{host}:{port}/docs")
    logger.info(f"OpenAPI Spec: http://{host}:{port}/swagger.json")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("=" * 60)

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
