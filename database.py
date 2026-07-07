import sqlite3
from datetime import datetime
import config

DATABASE_PATH = str(config.DATABASE_PATH)


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    config.init_dirs()
    conn = get_db()
    cursor = conn.cursor()

    # 笔记表
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

    # 每日数据记录表（简化：粉丝数 + 获赞与收藏）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            followers INTEGER DEFAULT 0,
            likes_and_saves INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()


# ============ 每日数据记录 ============

def add_daily_stat(date, followers, likes_and_saves):
    """添加或更新每日数据记录"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO daily_stats (date, followers, likes_and_saves)
        VALUES (?, ?, ?)
    ''', (date, followers, likes_and_saves))
    conn.commit()
    conn.close()


def get_daily_stats(limit=30):
    """获取每日数据记录，按日期倒序"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM daily_stats ORDER BY date DESC LIMIT ?
    ''', (limit,))
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stats


def get_daily_stats_for_chart(days=30):
    """获取用于图表的每日数据，按日期正序"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, followers, likes_and_saves
        FROM daily_stats
        ORDER BY date DESC
        LIMIT ?
    ''', (days,))
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stats[::-1]  # 反转为正序


def get_latest_daily_stat():
    """获取最新一条每日数据"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM daily_stats ORDER BY date DESC LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_daily_stat(stat_id):
    """删除每日数据记录"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM daily_stats WHERE id=?', (stat_id,))
    conn.commit()
    conn.close()


# ============ 笔记管理 ============

def add_note(title, content, note_type, publish_time, exposure, views,
             click_rate, likes, comments, saves, shares,
             followers_before, followers_after):
    """添加笔记"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notes (title, content, type, publish_time, exposure, views,
                          click_rate, likes, comments, saves, shares,
                          followers_before, followers_after)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, content, note_type, publish_time, exposure, views,
          click_rate, likes, comments, saves, shares,
          followers_before, followers_after))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id


def update_note(note_id, title, content, note_type, publish_time, exposure,
                views, click_rate, likes, comments, saves, shares,
                followers_before, followers_after):
    """更新笔记"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE notes SET title=?, content=?, type=?, publish_time=?,
               exposure=?, views=?, click_rate=?, likes=?, comments=?,
               saves=?, shares=?, followers_before=?, followers_after=?
        WHERE id=?
    ''', (title, content, note_type, publish_time, exposure, views,
          click_rate, likes, comments, saves, shares,
          followers_before, followers_after, note_id))
    conn.commit()
    conn.close()


def delete_note(note_id):
    """删除笔记"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id=?', (note_id,))
    conn.commit()
    conn.close()


def get_note(note_id):
    """获取单条笔记"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id=?', (note_id,))
    note = cursor.fetchone()
    conn.close()
    return dict(note) if note else None


def get_note_by_title(title):
    """根据标题查找笔记"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE title=?', (title,))
    note = cursor.fetchone()
    conn.close()
    return dict(note) if note else None


def get_all_notes(order_by='publish_time', order='DESC', note_type=None):
    """获取所有笔记"""
    conn = get_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM notes'
    params = []

    if note_type:
        query += ' WHERE type=?'
        params.append(note_type)

    allowed_columns = ['publish_time', 'exposure', 'views', 'likes',
                       'comments', 'saves', 'shares', 'created_at',
                       'followers_before', 'followers_after']
    if order_by in allowed_columns:
        order = 'DESC' if order.upper() == 'DESC' else 'ASC'
        query += f' ORDER BY {order_by} {order}'

    cursor.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes


def get_notes_for_chart():
    """获取笔记发布时间点，用于在趋势图上标注"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, publish_time,
               followers_before, followers_after,
               (followers_after - followers_before) as followers_gain
        FROM notes
        WHERE publish_time IS NOT NULL
        ORDER BY publish_time ASC
    ''')
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes


def get_overview_stats():
    """获取概览统计数据"""
    conn = get_db()
    cursor = conn.cursor()

    # 总笔记数
    cursor.execute('SELECT COUNT(*) as total_notes FROM notes')
    total_notes = cursor.fetchone()['total_notes']

    # 最新的每日数据
    cursor.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT 1')
    latest_stat = cursor.fetchone()

    conn.close()

    return {
        'total_notes': total_notes,
        'followers': latest_stat['followers'] if latest_stat else 0,
        'likes_and_saves': latest_stat['likes_and_saves'] if latest_stat else 0,
        'last_update': latest_stat['date'] if latest_stat else None
    }


# ============ 设置 ============

def get_setting(key):
    """获取设置"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None


def set_setting(key, value):
    """保存设置"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
    ''', (key, value))
    conn.commit()
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
