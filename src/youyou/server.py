"""YouYou 服务端 - RESTful API with OpenAPI/Swagger"""
import logging
import socket
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

from flask import Flask
from flask_restx import Api, Resource, fields
from flask_cors import CORS

from youyou.config import config
from youyou.agents.supervisor import supervisor
from youyou.agents.note_agent import note_agent
from youyou.core.zep_memory import get_zep_memory
from youyou.core.session_history import get_session_manager
from youyou.core.tag_parser import TagParser

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

chat_response_model = api.model('ChatResponse', {
    'response': fields.String(description='助手回复', example='好的，我已经记录了：钥匙放在书桌抽屉里。'),
    'timestamp': fields.String(description='时间戳', example='2025-11-05T12:00:00')
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


@ns_chat.route('/message')
class ChatMessage(Resource):
    """对话接口"""

    @ns_chat.doc('send_message')
    @ns_chat.expect(chat_request_model)
    @ns_chat.response(200, 'Success', chat_response_model)
    @ns_chat.response(400, 'Bad Request', error_model)
    @ns_chat.response(500, 'Internal Server Error', error_model)
    def post(self):
        """发送消息给助手

        支持的功能：
        - 记录物品位置：如 "钥匙放在书桌抽屉里"
        - 查询物品位置：如 "钥匙在哪？"
        - 列出所有物品：如 "我记录了哪些物品？"
        - 保存笔记：如 "#note 记录一个想法" 或 "https://github.com/..."
        - 日常对话：如 "你好"、"今天天气怎么样"
        """
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

                # 直接路由到指定 Agent（跳过 Supervisor）
                if parse_result.target_agent == "note_agent":
                    logger.info("🚀 直接调用 NoteAgent (跳过 Supervisor)...")
                    response = note_agent.invoke(parse_result.clean_message)
                    logger.info(f"📤 NoteAgent 返回响应 (前200字): {response[:200]}...")

                    # 保存会话历史
                    session_mgr = get_session_manager(max_history_length=10, refresh_interval=0)
                    session_mgr.add_interaction(
                        user_id=config.USER_ID,
                        user_input=user_input,
                        assistant_response=response,
                        agent_name="note_agent",
                        async_persist=True
                    )
                    logger.info("💾 交互已保存 (标记路由)")
                    logger.info("=" * 80)

                    return {
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    }

            # 2. 没有标记，走正常的 Supervisor 路由
            logger.info("🔄 未检测到标记，使用 Supervisor 路由...")

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

            # 提取响应 - 优先从 ToolMessage 提取，其次是 AIMessage
            messages_result = result.get("messages", [])
            response = ""

            if messages_result:
                # 倒序查找第一个有内容的消息
                for msg in reversed(messages_result):
                    msg_type = type(msg).__name__
                    content = getattr(msg, 'content', '')

                    if content and content.strip():
                        response = content
                        logger.info(f"从 {msg_type} 提取到响应: '{response[:100]}...'")
                        break

                if not response:
                    response = "抱歉,我无法处理这个请求"
                    logger.info("所有消息的 content 都为空")
            else:
                response = "抱歉,我无法处理这个请求"
                logger.info("消息列表为空")

            logger.info(f"📤 返回响应 (前200字): {response[:200]}...")

            # 更新会话历史 (内存 + 异步持久化到 Zep)
            session_mgr.add_interaction(
                user_id=user_id,
                user_input=user_input,
                assistant_response=response,
                agent_name="supervisor",
                async_persist=True  # 异步写入 Zep,不阻塞响应
            )
            logger.info("💾 交互已保存到内存并异步持久化到 Zep")
            logger.info("=" * 80)

            return {
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ 处理请求时出错: {e}")
            logger.error("详细错误信息:", exc_info=True)
            logger.error("=" * 80)
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
    host = "127.0.0.1"
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
