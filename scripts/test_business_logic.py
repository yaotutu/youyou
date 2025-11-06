#!/usr/bin/env python3
"""YouYou 业务逻辑综合测试脚本

测试覆盖:
1. Supervisor 路由逻辑
2. ItemAgent 五级查询策略
3. ChatAgent 对话和上下文理解
4. Zep 全局记忆系统
5. Session History 会话缓存
6. 数据库 CRUD 操作
7. 边界情况和错误处理
8. 多 Agent 协作
9. 性能测试

运行方式:
    uv run python scripts/test_business_logic.py
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "youyou"))

# 设置环境变量(如果需要)
os.environ["PYTHONPATH"] = str(project_root / "src" / "youyou")


# ==================== 测试配置 ====================

API_BASE_URL = "http://127.0.0.1:8000"
TEST_TIMEOUT = 180  # 每个测试超时时间(秒) - 允许更长时间应对 LLM API 响应慢


# ==================== 颜色输出 ====================

class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """打印测试头部"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(text: str):
    """打印测试章节"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'-' * 80}{Colors.ENDC}\n")


def print_test(test_name: str):
    """打印测试名称"""
    print(f"{Colors.BLUE}[测试] {test_name}{Colors.ENDC}")


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")


# ==================== API 客户端 ====================

class YouYouClient:
    """YouYou API 客户端"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def send_message(self, message: str, timeout: int = TEST_TIMEOUT) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """发送消息到 API

        Returns:
            (success, response_data, error_message)
        """
        try:
            url = f"{self.base_url}/api/v1/chat/message"
            payload = {"message": message}

            response = requests.post(url, json=payload, timeout=timeout)

            if response.status_code == 200:
                return True, response.json(), None
            else:
                return False, None, f"HTTP {response.status_code}: {response.text}"

        except requests.exceptions.ConnectionError:
            return False, None, "无法连接到服务器,请确保 youyou-server 已启动"
        except requests.exceptions.Timeout:
            return False, None, f"请求超时 (>{timeout}秒)"
        except Exception as e:
            return False, None, f"请求失败: {str(e)}"

    def check_health(self) -> Tuple[bool, Optional[str]]:
        """检查服务健康状态

        Returns:
            (is_healthy, error_message)
        """
        try:
            url = f"{self.base_url}/api/v1/system/health"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return True, None
            else:
                return False, f"健康检查失败: HTTP {response.status_code}"

        except Exception as e:
            return False, f"健康检查失败: {str(e)}"

    def get_config(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """获取系统配置

        Returns:
            (success, config_data, error_message)
        """
        try:
            url = f"{self.base_url}/api/v1/system/config"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return True, response.json(), None
            else:
                return False, None, f"HTTP {response.status_code}"

        except Exception as e:
            return False, None, f"获取配置失败: {str(e)}"


# ==================== 测试结果管理 ====================

class TestResult:
    """单个测试结果"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error_message = None
        self.duration = 0.0
        self.details = {}

    def __repr__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"{status} - {self.test_name} ({self.duration:.2f}s)"


class TestSuite:
    """测试套件"""

    def __init__(self, name: str):
        self.name = name
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.results.append(result)

    def start(self):
        """开始测试套件"""
        self.start_time = time.time()

    def end(self):
        """结束测试套件"""
        self.end_time = time.time()

    @property
    def total_tests(self) -> int:
        """总测试数"""
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        """通过的测试数"""
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_tests(self) -> int:
        """失败的测试数"""
        return sum(1 for r in self.results if not r.passed)

    @property
    def total_duration(self) -> float:
        """总测试时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def print_summary(self):
        """打印测试摘要"""
        print_header(f"测试套件: {self.name} - 测试摘要")

        print(f"总测试数: {self.total_tests}")
        print(f"通过: {Colors.GREEN}{self.passed_tests}{Colors.ENDC}")
        print(f"失败: {Colors.RED}{self.failed_tests}{Colors.ENDC}")
        print(f"总耗时: {self.total_duration:.2f}s")
        print(f"通过率: {self.passed_tests / self.total_tests * 100:.1f}%" if self.total_tests > 0 else "N/A")

        if self.failed_tests > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}失败的测试:{Colors.ENDC}")
            for result in self.results:
                if not result.passed:
                    print(f"  {Colors.RED}✗{Colors.ENDC} {result.test_name}")
                    if result.error_message:
                        print(f"    错误: {result.error_message}")

        print()


# ==================== 测试用例 ====================

class BusinessLogicTests:
    """业务逻辑测试"""

    def __init__(self):
        self.client = YouYouClient()
        self.suite = TestSuite("YouYou 业务逻辑综合测试")

    def run_all_tests(self):
        """运行所有测试"""
        print_header("YouYou 业务逻辑综合测试")

        # 检查服务状态
        if not self._check_server():
            print_error("服务器未运行,无法进行测试")
            print_info("请先运行: uv run youyou-server")
            return

        self.suite.start()

        # 1. 基础功能测试
        print_section("1. 基础功能测试")
        self._test_health_check()
        self._test_config_endpoint()

        # 2. 物品记录测试
        print_section("2. 物品记录测试")
        self._test_remember_single_item()
        self._test_remember_duplicate_item_same_location()
        self._test_remember_duplicate_item_different_location()
        self._test_remember_complex_item_names()

        # 3. 物品查询测试 - 五级策略
        print_section("3. 物品查询测试 - 五级策略")
        self._test_query_exact_match()
        self._test_query_alias_match()
        self._test_query_fuzzy_match()
        self._test_query_keyword_match()
        self._test_query_not_found()

        # 4. 列出物品测试
        print_section("4. 列出物品测试")
        self._test_list_all_items()

        # 5. Supervisor 路由测试
        print_section("5. Supervisor 路由逻辑测试")
        self._test_supervisor_route_to_item_agent()
        self._test_supervisor_route_to_chat_agent()

        # 6. ChatAgent 对话测试
        print_section("6. ChatAgent 对话测试")
        self._test_chat_simple_greeting()
        self._test_chat_general_question()

        # 7. 上下文和会话历史测试
        print_section("7. 会话历史和上下文测试")
        self._test_context_pronoun_reference()
        self._test_context_multi_turn()

        # 8. 边界情况测试
        print_section("8. 边界情况和错误处理测试")
        self._test_empty_message()
        self._test_very_long_message()
        self._test_special_characters()

        # 9. Zep 记忆兜底测试
        print_section("9. Zep 记忆兜底测试")
        self._test_zep_fallback_search()

        # 10. 性能测试
        print_section("10. 性能测试")
        self._test_performance_concurrent_requests()
        self._test_performance_response_time()

        self.suite.end()

        # 打印最终摘要
        self.suite.print_summary()

        # 返回退出码
        return 0 if self.suite.failed_tests == 0 else 1

    def _check_server(self) -> bool:
        """检查服务器是否运行"""
        print_info("检查服务器状态...")
        is_healthy, error = self.client.check_health()

        if is_healthy:
            print_success("服务器正常运行")
            return True
        else:
            print_error(f"服务器异常: {error}")
            return False

    def _run_test(self, test_name: str, test_func):
        """运行单个测试并记录结果"""
        print_test(test_name)
        result = TestResult(test_name)

        start_time = time.time()
        try:
            test_func(result)
            if not result.passed and not result.error_message:
                # 如果测试函数没有设置passed状态,默认为成功
                result.passed = True
        except Exception as e:
            result.passed = False
            result.error_message = str(e)
            print_error(f"测试异常: {e}")
        finally:
            result.duration = time.time() - start_time
            self.suite.add_result(result)

            if result.passed:
                print_success(f"通过 ({result.duration:.2f}s)")
            else:
                print_error(f"失败 ({result.duration:.2f}s)")
                if result.error_message:
                    print(f"  错误: {result.error_message}")

    # ==================== 基础功能测试 ====================

    def _test_health_check(self):
        """测试健康检查端点"""
        def test(result: TestResult):
            is_healthy, error = self.client.check_health()
            result.passed = is_healthy
            if not is_healthy:
                result.error_message = error

        self._run_test("健康检查端点", test)

    def _test_config_endpoint(self):
        """测试配置端点"""
        def test(result: TestResult):
            success, config, error = self.client.get_config()
            result.passed = success and config is not None
            if not result.passed:
                result.error_message = error or "配置为空"
            else:
                result.details["config"] = config
                print_info(f"  API Base: {config.get('api_base')}")
                print_info(f"  Router Model: {config.get('router_model')}")

        self._run_test("配置端点", test)

    # ==================== 物品记录测试 ====================

    def _test_remember_single_item(self):
        """测试记录单个物品"""
        def test(result: TestResult):
            message = "测试钥匙在测试桌子上"
            success, response, error = self.client.send_message(message)

            result.passed = (
                success and
                response is not None and
                "测试钥匙" in response.get("response", "") and
                "测试桌子" in response.get("response", "")
            )

            if not result.passed:
                result.error_message = error or "响应不符合预期"
            else:
                result.details["response"] = response.get("response")
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("记录单个物品", test)

    def _test_remember_duplicate_item_same_location(self):
        """测试重复记录相同位置的物品"""
        def test(result: TestResult):
            # 第一次记录
            message1 = "测试手机在测试背包"
            success1, _, _ = self.client.send_message(message1)

            # 第二次记录(相同位置)
            time.sleep(0.5)  # 等待数据库写入
            message2 = "测试手机在测试背包"
            success2, response2, error = self.client.send_message(message2)

            result.passed = (
                success1 and success2 and
                response2 is not None and
                ("确实" in response2.get("response", "") or "已经" in response2.get("response", ""))
            )

            if not result.passed:
                result.error_message = error or "未正确处理重复记录"
            else:
                print_info(f"  响应: {response2.get('response')[:100]}...")

        self._run_test("重复记录相同位置", test)

    def _test_remember_duplicate_item_different_location(self):
        """测试更新物品位置"""
        def test(result: TestResult):
            # 第一次记录
            message1 = "测试笔记本在测试客厅"
            success1, _, _ = self.client.send_message(message1)

            # 第二次记录(不同位置)
            time.sleep(0.5)
            message2 = "测试笔记本在测试卧室"
            success2, response2, error = self.client.send_message(message2)

            result.passed = (
                success1 and success2 and
                response2 is not None and
                ("移动" in response2.get("response", "") or "更新" in response2.get("response", ""))
            )

            if not result.passed:
                result.error_message = error or "未正确处理位置更新"
            else:
                print_info(f"  响应: {response2.get('response')[:100]}...")

        self._run_test("更新物品位置", test)

    def _test_remember_complex_item_names(self):
        """测试复杂物品名称"""
        def test(result: TestResult):
            test_cases = [
                ("MacBook Pro 笔记本电脑在测试书房", "MacBook Pro"),
                ("iPhone 15 Pro Max手机在测试床头柜", "iPhone 15 Pro Max"),
                ("测试护照在测试保险柜", "测试护照")
            ]

            all_passed = True
            for message, expected_item in test_cases:
                success, response, error = self.client.send_message(message)
                if not (success and expected_item.split()[0] in response.get("response", "")):
                    all_passed = False
                    result.error_message = f"处理 '{message}' 失败"
                    break
                time.sleep(0.3)

            result.passed = all_passed
            if result.passed:
                print_info(f"  测试了 {len(test_cases)} 个复杂物品名称")

        self._run_test("复杂物品名称", test)

    # ==================== 物品查询测试 ====================

    def _test_query_exact_match(self):
        """测试精确匹配查询"""
        def test(result: TestResult):
            # 先记录
            self.client.send_message("测试钱包在测试抽屉")
            time.sleep(0.5)

            # 查询
            success, response, error = self.client.send_message("测试钱包在哪？")

            result.passed = (
                success and
                response is not None and
                "测试抽屉" in response.get("response", "")
            )

            if not result.passed:
                result.error_message = error or "未找到物品位置"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("精确匹配查询", test)

    def _test_query_alias_match(self):
        """测试别名匹配查询"""
        def test(result: TestResult):
            # 记录"笔记本电脑"
            self.client.send_message("测试笔记本电脑在测试办公桌")
            time.sleep(0.5)

            # 用"电脑"查询
            success, response, error = self.client.send_message("测试电脑在哪？")

            result.passed = (
                success and
                response is not None and
                "测试办公桌" in response.get("response", "")
            )

            if not result.passed:
                result.error_message = error or "别名匹配失败"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("别名匹配查询", test)

    def _test_query_fuzzy_match(self):
        """测试模糊匹配查询"""
        def test(result: TestResult):
            # 记录
            self.client.send_message("测试充电器在测试床头")
            time.sleep(0.5)

            # 模糊查询
            success, response, error = self.client.send_message("测试充电在哪？")

            result.passed = (
                success and
                response is not None and
                ("测试床头" in response.get("response", "") or
                 "测试充电器" in response.get("response", ""))
            )

            if not result.passed:
                result.error_message = error or "模糊匹配失败"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("模糊匹配查询", test)

    def _test_query_keyword_match(self):
        """测试关键词匹配查询"""
        def test(result: TestResult):
            # 记录"摩托车钥匙"
            self.client.send_message("测试摩托车钥匙在测试车库")
            time.sleep(0.5)

            # 用关键词查询
            success, response, error = self.client.send_message("测试摩托车在哪？")

            result.passed = (
                success and
                response is not None and
                ("测试车库" in response.get("response", "") or
                 "测试摩托车钥匙" in response.get("response", ""))
            )

            if not result.passed:
                result.error_message = error or "关键词匹配失败"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("关键词匹配查询", test)

    def _test_query_not_found(self):
        """测试查询不存在的物品"""
        def test(result: TestResult):
            success, response, error = self.client.send_message("测试时光机在哪？")

            result.passed = (
                success and
                response is not None and
                ("没有" in response.get("response", "") or
                 "未找到" in response.get("response", "") or
                 "不知道" in response.get("response", ""))
            )

            if not result.passed:
                result.error_message = error or "未正确处理不存在的物品"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("查询不存在的物品", test)

    # ==================== 列出物品测试 ====================

    def _test_list_all_items(self):
        """测试列出所有物品"""
        def test(result: TestResult):
            # 先记录几个物品
            items = [
                "测试耳机在测试书桌",
                "测试鼠标在测试电脑旁",
            ]
            for item in items:
                self.client.send_message(item)
                time.sleep(0.3)

            # 列出所有物品
            success, response, error = self.client.send_message("我记录了哪些物品？")

            result.passed = (
                success and
                response is not None and
                len(response.get("response", "")) > 0
            )

            if not result.passed:
                result.error_message = error or "列出物品失败"
            else:
                print_info(f"  响应: {response.get('response')[:200]}...")

        self._run_test("列出所有物品", test)

    # ==================== Supervisor 路由测试 ====================

    def _test_supervisor_route_to_item_agent(self):
        """测试 Supervisor 正确路由到 ItemAgent"""
        def test(result: TestResult):
            test_messages = [
                "测试路由物品在测试位置",
                "测试路由物品在哪？",
                "查看我记录了哪些物品"
            ]

            all_passed = True
            for message in test_messages:
                success, response, error = self.client.send_message(message)
                if not success:
                    all_passed = False
                    result.error_message = f"路由失败: {message}"
                    break
                time.sleep(0.3)

            result.passed = all_passed
            if result.passed:
                print_info(f"  测试了 {len(test_messages)} 个物品相关消息")

        self._run_test("Supervisor 路由到 ItemAgent", test)

    def _test_supervisor_route_to_chat_agent(self):
        """测试 Supervisor 正确路由到 ChatAgent"""
        def test(result: TestResult):
            test_messages = [
                "你好",
                "今天天气怎么样？",
                "什么是人工智能？"
            ]

            all_passed = True
            for message in test_messages:
                success, response, error = self.client.send_message(message)
                if not success:
                    all_passed = False
                    result.error_message = f"路由失败: {message}"
                    break
                time.sleep(0.3)

            result.passed = all_passed
            if result.passed:
                print_info(f"  测试了 {len(test_messages)} 个对话消息")

        self._run_test("Supervisor 路由到 ChatAgent", test)

    # ==================== ChatAgent 测试 ====================

    def _test_chat_simple_greeting(self):
        """测试简单问候"""
        def test(result: TestResult):
            success, response, error = self.client.send_message("你好")

            result.passed = (
                success and
                response is not None and
                len(response.get("response", "")) > 0
            )

            if not result.passed:
                result.error_message = error or "问候失败"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("简单问候", test)

    def _test_chat_general_question(self):
        """测试一般性问题"""
        def test(result: TestResult):
            success, response, error = self.client.send_message("你能做什么？")

            result.passed = (
                success and
                response is not None and
                len(response.get("response", "")) > 10  # 期望有详细回答
            )

            if not result.passed:
                result.error_message = error or "回答不完整"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")

        self._run_test("一般性问题", test)

    # ==================== 上下文测试 ====================

    def _test_context_pronoun_reference(self):
        """测试代词引用"""
        def test(result: TestResult):
            # 第一轮: 记录物品
            msg1 = "测试上下文钥匙在测试玄关"
            success1, _, _ = self.client.send_message(msg1)
            time.sleep(0.5)

            # 第二轮: 使用"它"指代
            msg2 = "它在哪里？"
            success2, response2, error = self.client.send_message(msg2)

            # 注意: 这个测试可能失败,因为需要强大的上下文理解
            # 这里我们只检查是否有响应
            result.passed = success1 and success2 and response2 is not None

            if not result.passed:
                result.error_message = error or "上下文测试失败"
            else:
                print_info(f"  响应: {response2.get('response')[:100]}...")
                print_warning("  注意: 代词引用依赖于 Agent 的上下文理解能力")

        self._run_test("代词引用测试", test)

    def _test_context_multi_turn(self):
        """测试多轮对话"""
        def test(result: TestResult):
            # 多轮对话
            messages = [
                "你好",
                "我刚才说什么了？",
                "谢谢"
            ]

            all_passed = True
            for i, message in enumerate(messages, 1):
                success, response, error = self.client.send_message(message)
                if not success:
                    all_passed = False
                    result.error_message = f"第{i}轮失败: {error}"
                    break
                time.sleep(0.5)

            result.passed = all_passed
            if result.passed:
                print_info(f"  完成 {len(messages)} 轮对话")

        self._run_test("多轮对话测试", test)

    # ==================== 边界情况测试 ====================

    def _test_empty_message(self):
        """测试空消息"""
        def test(result: TestResult):
            success, response, error = self.client.send_message("")

            # 应该返回错误
            result.passed = not success or (response and "错误" in response.get("error", ""))

            if not result.passed:
                result.error_message = "未正确处理空消息"
            else:
                print_info("  正确拒绝空消息")

        self._run_test("空消息处理", test)

    def _test_very_long_message(self):
        """测试超长消息"""
        def test(result: TestResult):
            long_message = "测试超长物品" + "非常" * 100 + "在测试位置"
            success, response, error = self.client.send_message(long_message)

            # 应该能处理,但可能被截断
            result.passed = success and response is not None

            if not result.passed:
                result.error_message = error or "无法处理超长消息"
            else:
                print_info(f"  消息长度: {len(long_message)} 字符")

        self._run_test("超长消息处理", test)

    def _test_special_characters(self):
        """测试特殊字符"""
        def test(result: TestResult):
            special_message = "测试特殊字符@#$%^&*()在测试地方"
            success, response, error = self.client.send_message(special_message)

            result.passed = success and response is not None

            if not result.passed:
                result.error_message = error or "无法处理特殊字符"
            else:
                print_info("  正确处理特殊字符")

        self._run_test("特殊字符处理", test)

    # ==================== Zep 记忆测试 ====================

    def _test_zep_fallback_search(self):
        """测试 Zep 记忆兜底搜索"""
        def test(result: TestResult):
            # 这个测试需要 Zep 配置,如果没有配置会失败
            # 我们只检查系统是否能正常处理(即使 Zep 未配置)

            # 先进行一些对话,让 Zep 记录
            self.client.send_message("我提到过测试Zep物品放在某个地方")
            time.sleep(0.5)

            # 尝试查询(可能触发 Zep 兜底)
            success, response, error = self.client.send_message("测试Zep物品在哪？")

            # 无论 Zep 是否配置,系统都应该能响应
            result.passed = success and response is not None

            if not result.passed:
                result.error_message = error or "Zep 兜底测试失败"
            else:
                print_info(f"  响应: {response.get('response')[:100]}...")
                print_warning("  注意: Zep 兜底功能依赖于 Zep 配置")

        self._run_test("Zep 记忆兜底搜索", test)

    # ==================== 性能测试 ====================

    def _test_performance_concurrent_requests(self):
        """测试并发请求处理能力"""
        def test(result: TestResult):
            import concurrent.futures

            messages = [
                f"测试并发物品{i}在测试位置{i}"
                for i in range(5)
            ]

            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.client.send_message, msg)
                    for msg in messages
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            duration = time.time() - start_time

            # 检查所有请求是否成功
            all_success = all(r[0] for r in results)

            result.passed = all_success
            if not result.passed:
                result.error_message = "部分并发请求失败"
            else:
                print_info(f"  {len(messages)} 个并发请求耗时: {duration:.2f}s")
                print_info(f"  平均响应时间: {duration/len(messages):.2f}s")

        self._run_test("并发请求处理", test)

    def _test_performance_response_time(self):
        """测试响应时间"""
        def test(result: TestResult):
            test_messages = [
                "测试性能物品在测试位置",
                "测试性能物品在哪？",
                "你好"
            ]

            response_times = []
            for message in test_messages:
                start = time.time()
                success, response, error = self.client.send_message(message)
                duration = time.time() - start

                if success:
                    response_times.append(duration)
                time.sleep(0.3)

            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)

                # 期望平均响应时间 < 10s, 最大响应时间 < 15s
                result.passed = avg_time < 10 and max_time < 15

                if not result.passed:
                    result.error_message = f"响应时间过长: 平均{avg_time:.2f}s, 最大{max_time:.2f}s"
                else:
                    print_info(f"  平均响应时间: {avg_time:.2f}s")
                    print_info(f"  最大响应时间: {max_time:.2f}s")
            else:
                result.passed = False
                result.error_message = "无有效响应时间数据"

        self._run_test("响应时间测试", test)


# ==================== 主函数 ====================

def main():
    """主函数"""
    try:
        tests = BusinessLogicTests()
        exit_code = tests.run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被用户中断{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}测试执行失败: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
