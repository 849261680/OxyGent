"""
用于浏览器操作的 MCP 服务器

该包提供可由代理调用的浏览器自动化工具。  
它包含用于网页导航、元素交互、截图捕获、浏览器标签管理，  
以及基于 Playwright 框架的自动登录功能。
"""


from .core import mcp, check_dependencies
from .navigation import (
    browser_navigate,
    browser_navigate_back,
    browser_navigate_forward
)
from .interaction import (
    browser_click,
    browser_hover,
    browser_type
)
from .content import (
    browser_snapshot,
    browser_take_screenshot
)
from .tabs import (
    browser_tab_list,
    browser_tab_new,
    browser_tab_close
)
from .login import (
    browser_auto_login
)
from .search import (
    browser_search
)
from .core import (
    browser_check_status
)

# 导出所有工具函数，方便导入
__all__ = [
    'mcp',
    'check_dependencies',
    'browser_navigate',
    'browser_navigate_back',
    'browser_navigate_forward',
    'browser_click',
    'browser_hover',
    'browser_type',
    'browser_snapshot',
    'browser_take_screenshot',
    'browser_tab_list',
    'browser_tab_new',
    'browser_tab_close',
    'browser_auto_login',
    'browser_search',
    'browser_check_status'
]
