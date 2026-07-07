"""
小红书运营分析工具 - 配置文件模板
复制此文件为 config.py 并填入你的配置
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent

# 数据存储路径
DATA_DIR = BASE_DIR / "data"

# 数据库配置
# 使用云数据库（Supabase PostgreSQL）实现多设备同步
USE_CLOUD_DB = True  # 改为 False 使用本地SQLite

# Supabase 连接参数 - 填入你的Supabase信息
SUPABASE_HOST = "your-project.pooler.supabase.com"
SUPABASE_PORT = 6543
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres.your-project-id"
SUPABASE_PASSWORD = "your-password"

# Supabase PostgreSQL 连接字符串 (备用)
SUPABASE_DB_URL = f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DATABASE}"

# 本地SQLite数据库路径（备用）
LOCAL_DATABASE_PATH = DATA_DIR / "notes.db"

# 浏览器数据路径（用于保持登录状态，始终在本地）
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
