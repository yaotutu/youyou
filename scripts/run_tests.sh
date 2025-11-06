#!/bin/bash
# YouYou 测试快速运行脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}YouYou 测试快速运行脚本${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${RED}错误: 未找到 .env 文件${NC}"
    echo -e "${YELLOW}请先复制并配置 .env.example:${NC}"
    echo "  cp .env.example .env"
    echo "  vim .env  # 配置 API Key 等"
    exit 1
fi

# 检查服务是否运行
echo -e "${BLUE}检查服务状态...${NC}"
if curl -s -f http://127.0.0.1:8000/api/v1/system/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 服务已运行${NC}"
    RUN_TESTS_ONLY=true
else
    echo -e "${YELLOW}⚠ 服务未运行${NC}"
    RUN_TESTS_ONLY=false
fi
echo ""

# 如果服务未运行,询问是否启动
if [ "$RUN_TESTS_ONLY" = false ]; then
    echo -e "${YELLOW}需要先启动 youyou-server${NC}"
    echo "选项:"
    echo "  1) 自动启动服务并运行测试 (推荐)"
    echo "  2) 仅给出手动启动指令,退出脚本"
    echo "  3) 取消"
    echo ""
    read -p "请选择 [1-3]: " choice

    case $choice in
        1)
            echo -e "${BLUE}启动 youyou-server...${NC}"
            # 后台启动服务
            uv run youyou-server > youyou-server.log 2>&1 &
            SERVER_PID=$!
            echo "服务进程 PID: $SERVER_PID"

            # 等待服务启动
            echo "等待服务启动..."
            for i in {1..30}; do
                if curl -s -f http://127.0.0.1:8000/api/v1/system/health > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ 服务启动成功${NC}"
                    break
                fi
                echo -n "."
                sleep 1
            done
            echo ""

            # 再次检查
            if ! curl -s -f http://127.0.0.1:8000/api/v1/system/health > /dev/null 2>&1; then
                echo -e "${RED}✗ 服务启动失败${NC}"
                echo "请查看日志: tail youyou-server.log"
                if [ -n "$SERVER_PID" ]; then
                    kill $SERVER_PID 2>/dev/null || true
                fi
                exit 1
            fi

            AUTO_STARTED=true
            ;;
        2)
            echo ""
            echo -e "${YELLOW}请在另一个终端运行:${NC}"
            echo "  cd $PROJECT_ROOT"
            echo "  uv run youyou-server"
            echo ""
            echo "然后重新运行此脚本:"
            echo "  ./scripts/run_tests.sh"
            exit 0
            ;;
        *)
            echo "已取消"
            exit 0
            ;;
    esac
fi

# 运行测试
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}运行测试...${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

uv run python scripts/test_business_logic.py
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}测试完成${NC}"
echo -e "${BLUE}======================================${NC}"

# 如果是自动启动的服务,询问是否关闭
if [ "${AUTO_STARTED:-false}" = true ]; then
    echo ""
    read -p "是否关闭自动启动的服务? [y/N]: " close_server
    if [[ $close_server =~ ^[Yy]$ ]]; then
        if [ -n "$SERVER_PID" ]; then
            echo "关闭服务 (PID: $SERVER_PID)..."
            kill $SERVER_PID 2>/dev/null || true
            echo -e "${GREEN}✓ 服务已关闭${NC}"
        fi
    else
        echo -e "${YELLOW}服务仍在后台运行 (PID: $SERVER_PID)${NC}"
        echo "日志文件: youyou-server.log"
        echo "关闭服务: kill $SERVER_PID"
    fi
fi

# 退出码
exit $TEST_EXIT_CODE
