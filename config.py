"""
小红书运营分析工具 - 配置文件
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent

# 数据存储路径 - 可以改为iCloud路径实现多设备同步
# 例如: Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/xiaohongshu-data"
DATA_DIR = BASE_DIR / "data"

# 数据库路径
DATABASE_PATH = DATA_DIR / "notes.db"

# 浏览器数据路径（用于保持登录状态）
BROWSER_DATA_DIR = DATA_DIR / "browser_data"

# Flask配置
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# 爬虫配置
SCRAPER_TIMEOUT = 30000  # 页面加载超时（毫秒）
SCRAPER_SCROLL_DELAY = 0.6  # 滚动间隔（秒）
SCRAPER_MAX_SCROLLS = 200  # 最大滚动次数

# 确保数据目录存在
def init_dirs():
    """初始化必要的目录"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)
