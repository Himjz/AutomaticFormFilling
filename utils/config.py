# config.py
import os

# 表单配置
FORM_CONFIG = {
    "url": "https://f.wps.cn/ksform/w/write/9ZhYHYlD",
    "field_map": {
        "学号": "学号",
        "专业班级": "专业班级",
        "姓名": "姓名",
        "联系方式": "联系方式",
        "QQ号": "QQ号"
    },
    "selectors": {
        "submit_btn": "button.src-components-write-footer-index__submitBtn",
        "confirm_btn": "div.ant-modal-footer button:has-text('确 认')"
    }
}

# 路径配置
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
DATA_FILE = os.path.join(BASE_DIR, "form_data.json")
ICON_PATH = os.path.join(BASE_DIR, "resource", "aff.ico")

# 异步配置
ASYNC_CONFIG = {
    "timeout": 10,  # 页面加载超时（秒）
    "submit_delay": 1,  # 提交确认后延时（秒）
    "max_concurrent": 3,  # 最大并发数
    "check_interval": 0.1  # 定时检查间隔（秒）
}

# 浏览器配置
BROWSER_CONFIG = {
    "headless": False,
    "args": [
        "--disable-gpu",
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--start-maximized"
    ]
}