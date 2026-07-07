"""
小红书运营分析工具 - 配置文件
支持环境变量配置（用于Vercel等云部署）
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent

# 数据存储路径
DATA_DIR = BASE_DIR / "data"

# 数据库配置 - 从环境变量读取，支持云部署
USE_CLOUD_DB = os.environ.get("USE_CLOUD_DB", "true").lower() == "true"

# Supabase 连接参数 - 从环境变量读取
SUPABASE_HOST = os.environ.get("SUPABASE_HOST", "")
SUPABASE_PORT = int(os.environ.get("SUPABASE_PORT", "6543"))
SUPABASE_DATABASE = os.environ.get("SUPABASE_DATABASE", "postgres")
SUPABASE_USER = os.environ.get("SUPABASE_USER", "")
SUPABASE_PASSWORD = os.environ.get("SUPABASE_PASSWORD", "")

# 本地SQLite数据库路径（备用）
LOCAL_DATABASE_PATH = DATA_DIR / "notes.db"

# 浏览器数据路径（用于保持登录状态，始终在本地）
BROWSER_DATA_DIR = DATA_DIR / "browser_data"

# Flask配置
FLASK_HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# 爬虫配置
SCRAPER_TIMEOUT = 30000
SCRAPER_SCROLL_DELAY = 0.6
SCRAPER_MAX_SCROLLS = 200

# 确保数据目录存在
def init_dirs():
    """初始化必要的目录"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)
