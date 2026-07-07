"""
数据库模块 - 支持本地SQLite和云端PostgreSQL
"""
import sqlite3
from datetime import datetime
import config

# 根据配置选择数据库类型
if config.USE_CLOUD_DB:
    import psycopg2
    from psycopg2.extras import RealDictCursor


def get_db():
    """获取数据库连接"""
    if config.USE_CLOUD_DB:
        conn = psycopg2.connect(
            host=config.SUPABASE_HOST,
            port=config.SUPABASE_PORT,
            database=config.SUPABASE_DATABASE,
            user=config.SUPABASE_USER,
            password=config.SUPABASE_PASSWORD
        )
        return conn
    else:
        conn = sqlite3.connect(str(config.LOCAL_DATABASE_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def execute_query(query, params=None, fetch=False, fetchone=False):
    """执行查询的通用函数"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # PostgreSQL 使用 %s 占位符
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
    else:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

    result = None
    if fetchone:
        row = cursor.fetchone()
        result = dict(row) if row else None
    elif fetch:
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]

    if not fetch and not fetchone:
        conn.commit()
        # 获取最后插入的ID
        if config.USE_CLOUD_DB and 'INSERT' in query.upper():
            cursor.execute("SELECT lastval()")
            result = cursor.fetchone()['lastval']
        elif not config.USE_CLOUD_DB and 'INSERT' in query.upper():
            result = cursor.lastrowid

    cursor.close()
    conn.close()
    return result


def init_db():
    """初始化数据库表"""
    config.init_dirs()
    conn = get_db()
    cursor = conn.cursor()

    if config.USE_CLOUD_DB:
        # PostgreSQL 语法
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT,
                publish_time TIMESTAMP,
                exposure INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                click_rate REAL DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                followers_before INTEGER DEFAULT 0,
                followers_after INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                followers INTEGER DEFAULT 0,
                likes_and_saves INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
    else:
        # SQLite 语法
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT,
                publish_time DATETIME,
                exposure INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                click_rate REAL DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                followers_before INTEGER DEFAULT 0,
                followers_after INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                followers INTEGER DEFAULT 0,
                likes_and_saves INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

    conn.commit()
    cursor.close()
    conn.close()


# ============ 每日数据记录 ============

def add_daily_stat(date, followers, likes_and_saves):
    """添加或更新每日数据记录"""
    conn = get_db()
    cursor = conn.cursor()

    if config.USE_CLOUD_DB:
        cursor.execute('''
            INSERT INTO daily_stats (date, followers, likes_and_saves)
            VALUES (%s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                followers = EXCLUDED.followers,
                likes_and_saves = EXCLUDED.likes_and_saves
        ''', (date, followers, likes_and_saves))
    else:
        cursor.execute('''
            INSERT OR REPLACE INTO daily_stats (date, followers, likes_and_saves)
            VALUES (?, ?, ?)
        ''', (date, followers, likes_and_saves))

    conn.commit()
    cursor.close()
    conn.close()


def get_daily_stats(limit=30):
    """获取每日数据记录，按日期倒序"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT %s', (limit,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT ?', (limit,))

    rows = cursor.fetchall()
    stats = [dict(row) for row in rows]

    # 转换日期格式
    for stat in stats:
        if stat.get('date') and hasattr(stat['date'], 'isoformat'):
            stat['date'] = stat['date'].isoformat()

    cursor.close()
    conn.close()
    return stats


def get_daily_stats_for_chart(days=30):
    """获取用于图表的每日数据，按日期正序"""
    stats = get_daily_stats(days)
    return stats[::-1]


def get_latest_daily_stat():
    """获取最新一条每日数据"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT 1')
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT 1')

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def delete_daily_stat(stat_id):
    """删除每日数据记录"""
    conn = get_db()
    cursor = conn.cursor()

    if config.USE_CLOUD_DB:
        cursor.execute('DELETE FROM daily_stats WHERE id=%s', (stat_id,))
    else:
        cursor.execute('DELETE FROM daily_stats WHERE id=?', (stat_id,))

    conn.commit()
    cursor.close()
    conn.close()


# ============ 笔记管理 ============

def add_note(title, content, note_type, publish_time, exposure, views,
             click_rate, likes, comments, saves, shares,
             followers_before, followers_after):
    """添加笔记"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            INSERT INTO notes (title, content, type, publish_time, exposure, views,
                              click_rate, likes, comments, saves, shares,
                              followers_before, followers_after)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (title, content, note_type, publish_time, exposure, views,
              click_rate, likes, comments, saves, shares,
              followers_before, followers_after))
        note_id = cursor.fetchone()['id']
    else:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notes (title, content, type, publish_time, exposure, views,
                              click_rate, likes, comments, saves, shares,
                              followers_before, followers_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, note_type, publish_time, exposure, views,
              click_rate, likes, comments, saves, shares,
              followers_before, followers_after))
        note_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return note_id


def update_note(note_id, title, content, note_type, publish_time, exposure,
                views, click_rate, likes, comments, saves, shares,
                followers_before, followers_after):
    """更新笔记"""
    conn = get_db()
    cursor = conn.cursor()

    if config.USE_CLOUD_DB:
        cursor.execute('''
            UPDATE notes SET title=%s, content=%s, type=%s, publish_time=%s,
                   exposure=%s, views=%s, click_rate=%s, likes=%s, comments=%s,
                   saves=%s, shares=%s, followers_before=%s, followers_after=%s
            WHERE id=%s
        ''', (title, content, note_type, publish_time, exposure, views,
              click_rate, likes, comments, saves, shares,
              followers_before, followers_after, note_id))
    else:
        cursor.execute('''
            UPDATE notes SET title=?, content=?, type=?, publish_time=?,
                   exposure=?, views=?, click_rate=?, likes=?, comments=?,
                   saves=?, shares=?, followers_before=?, followers_after=?
            WHERE id=?
        ''', (title, content, note_type, publish_time, exposure, views,
              click_rate, likes, comments, saves, shares,
              followers_before, followers_after, note_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_note(note_id):
    """删除笔记"""
    conn = get_db()
    cursor = conn.cursor()

    if config.USE_CLOUD_DB:
        cursor.execute('DELETE FROM notes WHERE id=%s', (note_id,))
    else:
        cursor.execute('DELETE FROM notes WHERE id=?', (note_id,))

    conn.commit()
    cursor.close()
    conn.close()


def get_note(note_id):
    """获取单条笔记"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM notes WHERE id=%s', (note_id,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notes WHERE id=?', (note_id,))

    note = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(note) if note else None


def get_note_by_title(title):
    """根据标题查找笔记"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM notes WHERE title=%s', (title,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notes WHERE title=?', (title,))

    note = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(note) if note else None


def get_all_notes(order_by='publish_time', order='DESC', note_type=None):
    """获取所有笔记"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()

    allowed_columns = ['publish_time', 'exposure', 'views', 'likes',
                       'comments', 'saves', 'shares', 'created_at',
                       'followers_before', 'followers_after']

    if order_by not in allowed_columns:
        order_by = 'publish_time'
    order = 'DESC' if order.upper() == 'DESC' else 'ASC'

    if note_type:
        if config.USE_CLOUD_DB:
            cursor.execute(f'SELECT * FROM notes WHERE type=%s ORDER BY {order_by} {order}', (note_type,))
        else:
            cursor.execute(f'SELECT * FROM notes WHERE type=? ORDER BY {order_by} {order}', (note_type,))
    else:
        cursor.execute(f'SELECT * FROM notes ORDER BY {order_by} {order}')

    rows = cursor.fetchall()
    notes = [dict(row) for row in rows]
    cursor.close()
    conn.close()
    return notes


def get_notes_for_chart():
    """获取笔记发布时间点，用于在趋势图上标注"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()

    cursor.execute('''
        SELECT id, title, publish_time,
               followers_before, followers_after,
               (followers_after - followers_before) as followers_gain
        FROM notes
        WHERE publish_time IS NOT NULL
        ORDER BY publish_time ASC
    ''')

    rows = cursor.fetchall()
    notes = [dict(row) for row in rows]
    cursor.close()
    conn.close()
    return notes


def get_overview_stats():
    """获取概览统计数据"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total_notes FROM notes')
    row = cursor.fetchone()
    total_notes = row['total_notes'] if row else 0

    cursor.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT 1')
    row = cursor.fetchone()
    latest_stat = dict(row) if row else None

    cursor.close()
    conn.close()

    result = {
        'total_notes': total_notes,
        'followers': latest_stat['followers'] if latest_stat else 0,
        'likes_and_saves': latest_stat['likes_and_saves'] if latest_stat else 0,
        'last_update': None
    }

    if latest_stat and latest_stat.get('date'):
        date_val = latest_stat['date']
        if hasattr(date_val, 'isoformat'):
            result['last_update'] = date_val.isoformat()
        else:
            result['last_update'] = str(date_val)

    return result


# ============ 设置 ============

def get_setting(key):
    """获取设置"""
    conn = get_db()

    if config.USE_CLOUD_DB:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT value FROM settings WHERE key=%s', (key,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key=?', (key,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['value'] if row else None


def set_setting(key, value):
    """保存设置"""
    conn = get_db()
    cursor = conn.cursor()

    if config.USE_CLOUD_DB:
        cursor.execute('''
            INSERT INTO settings (key, value) VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        ''', (key, value))
    else:
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))

    conn.commit()
    cursor.close()
    conn.close()


# ============ 导出 ============

def export_notes_json():
    """导出笔记为JSON"""
    return get_all_notes()


def export_notes_csv():
    """导出笔记为CSV"""
    import csv
    import io

    notes = get_all_notes()
    if not notes:
        return ''

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=notes[0].keys())
    writer.writeheader()
    writer.writerows(notes)
    return output.getvalue()
