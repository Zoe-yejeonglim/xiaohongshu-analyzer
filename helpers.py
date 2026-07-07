"""
小红书运营分析工具 - 辅助函数
"""
from datetime import datetime
import database


def save_scraped_data(notes, account_info):
    """
    保存爬取的数据到数据库

    Args:
        notes: 笔记列表
        account_info: 账号信息 {'followers': int, 'likes_and_saves': int}

    Returns:
        int: 成功导入的笔记数量
    """
    # 更新每日统计
    if account_info.get('followers') or account_info.get('likes_and_saves'):
        today = datetime.now().strftime('%Y-%m-%d')
        database.add_daily_stat(
            today,
            account_info.get('followers', 0),
            account_info.get('likes_and_saves', 0)
        )

    # 更新笔记数据
    imported = 0
    for note in notes:
        try:
            existing = database.get_note_by_title(note.get('title', ''))

            note_data = {
                'title': note.get('title', ''),
                'content': '',
                'note_type': note.get('type', '图文'),
                'publish_time': note.get('publish_time'),
                'exposure': note.get('exposure', 0),
                'views': note.get('views', 0),
                'click_rate': note.get('click_rate', 0),
                'likes': note.get('likes', 0),
                'comments': note.get('comments', 0),
                'saves': note.get('saves', 0),
                'shares': note.get('shares', 0),
            }

            if existing:
                database.update_note(
                    note_id=existing['id'],
                    followers_before=existing.get('followers_before', 0),
                    followers_after=existing.get('followers_after', 0),
                    **note_data
                )
            else:
                database.add_note(
                    followers_before=0,
                    followers_after=0,
                    **note_data
                )
            imported += 1
        except Exception:
            continue

    return imported
