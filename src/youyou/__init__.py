"""
YouYou 包入口
为了兼容 uv 的包管理，这个文件重新导出主模块
"""

# 重新导出主要组件，保持向后兼容
import sys
from pathlib import Path

# 将 src/ 目录添加到路径，这样可以从 src/ 导入
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 重新导出核心模块
from config import *
from server import *

__all__ = ['config', 'server']
