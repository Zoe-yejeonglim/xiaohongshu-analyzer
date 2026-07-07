import os
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
from datetime import datetime
import re
import config
import database
import ai_analyzer
from helpers import save_scraped_data

# Vercel环境不加载scraper（需要浏览器）
IS_VERCEL = os.environ.get("VERCEL")
if not IS_VERCEL:
    import scraper
else:
    scraper = None

app = Flask(__name__)


@app.before_request
def before_first_request():
    """Initialize database on first request."""
    database.init_db()


@app.route('/')
def index():
    """首页 - 数据概况和涨粉趋势"""
    overview = database.get_overview_stats()
    daily_stats = database.get_daily_stats(limit=10)
    chart_data = database.get_daily_stats_for_chart(days=30)
    notes_for_chart = database.get_notes_for_chart()
    return render_template('index.html',
                           overview=overview,
                           daily_stats=daily_stats,
                           chart_data=chart_data,
                           notes_for_chart=notes_for_chart)


@app.route('/daily-stats/add', methods=['POST'])
def add_daily_stat():
    """添加每日数据记录"""
    data = request.form
    date = data.get('date')
    followers = int(data.get('followers', 0) or 0)
    likes_and_saves = int(data.get('likes_and_saves', 0) or 0)

    database.add_daily_stat(date, followers, likes_and_saves)
    return redirect(url_for('index'))


@app.route('/daily-stats/<int:stat_id>/delete', methods=['POST'])
def delete_daily_stat(stat_id):
    """删除每日数据记录"""
    database.delete_daily_stat(stat_id)
    return jsonify({'success': True})


@app.route('/notes')
def notes():
    """笔记列表页"""
    order_by = request.args.get('order_by', 'publish_time')
    order = request.args.get('order', 'DESC')
    note_type = request.args.get('type', None)
    all_notes = database.get_all_notes(order_by=order_by, order=order, note_type=note_type)
    return render_template('notes.html', notes=all_notes)


@app.route('/notes/add', methods=['GET', 'POST'])
def add_note():
    """添加笔记"""
    if request.method == 'POST':
        data = request.form
        database.add_note(
            title=data.get('title', ''),
            content=data.get('content', ''),
            note_type=data.get('type', '图文'),
            publish_time=data.get('publish_time') or None,
            exposure=int(data.get('exposure', 0) or 0),
            views=int(data.get('views', 0) or 0),
            click_rate=float(data.get('click_rate', 0) or 0),
            likes=int(data.get('likes', 0) or 0),
            comments=int(data.get('comments', 0) or 0),
            saves=int(data.get('saves', 0) or 0),
            shares=int(data.get('shares', 0) or 0),
            followers_before=int(data.get('followers_before', 0) or 0),
            followers_after=int(data.get('followers_after', 0) or 0)
        )
        return redirect(url_for('notes'))
    return render_template('add_note.html')


@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
def edit_note(note_id):
    """编辑笔记"""
    note = database.get_note(note_id)
    if not note:
        return redirect(url_for('notes'))

    if request.method == 'POST':
        data = request.form
        database.update_note(
            note_id=note_id,
            title=data.get('title', ''),
            content=data.get('content', ''),
            note_type=data.get('type', '图文'),
            publish_time=data.get('publish_time') or None,
            exposure=int(data.get('exposure', 0) or 0),
            views=int(data.get('views', 0) or 0),
            click_rate=float(data.get('click_rate', 0) or 0),
            likes=int(data.get('likes', 0) or 0),
            comments=int(data.get('comments', 0) or 0),
            saves=int(data.get('saves', 0) or 0),
            shares=int(data.get('shares', 0) or 0),
            followers_before=int(data.get('followers_before', 0) or 0),
            followers_after=int(data.get('followers_after', 0) or 0)
        )
        return redirect(url_for('notes'))
    return render_template('add_note.html', note=note, edit=True)


@app.route('/notes/<int:note_id>/delete', methods=['POST'])
def delete_note(note_id):
    """删除笔记"""
    database.delete_note(note_id)
    return jsonify({'success': True})


def parse_xiaohongshu_time(time_str):
    """解析小红书导出的时间格式，如：2026年06月05日17时46分16秒"""
    if not time_str or pd.isna(time_str):
        return None
    try:
        # 尝试匹配小红书格式
        match = re.match(r'(\d{4})年(\d{2})月(\d{2})日(\d{2})时(\d{2})分(\d{2})秒', str(time_str))
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
        # 尝试其他常见格式
        return str(time_str)
    except:
        return None


@app.route('/notes/import', methods=['POST'])
def import_notes():
    """从Excel导入笔记（兼容小红书创作者中心导出格式）"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    try:
        # 读取Excel，跳过第一行（那是标题说明行）
        df = pd.read_excel(file, header=1)

        # 小红书创作者中心导出的列名映射
        column_map = {
            # 标题
            '笔记标题': 'title',
            '标题': 'title',
            'title': 'title',
            # 发布时间
            '首次发布时间': 'publish_time',
            '发布时间': 'publish_time',
            'publish_time': 'publish_time',
            # 类型
            '体裁': 'type',
            '类型': 'type',
            'type': 'type',
            # 曝光
            '曝光': 'exposure',
            '曝光量': 'exposure',
            'exposure': 'exposure',
            # 观看
            '观看量': 'views',
            '观看': 'views',
            '播放': 'views',
            'views': 'views',
            # 点击率
            '封面点击率': 'click_rate',
            '点击率': 'click_rate',
            'click_rate': 'click_rate',
            # 点赞
            '点赞': 'likes',
            '点赞数': 'likes',
            'likes': 'likes',
            # 评论
            '评论': 'comments',
            '评论数': 'comments',
            'comments': 'comments',
            # 收藏
            '收藏': 'saves',
            '收藏数': 'saves',
            'saves': 'saves',
            # 分享
            '分享': 'shares',
            '分享数': 'shares',
            'shares': 'shares',
            # 涨粉（小红书导出有这个字段，但我们用发布前后粉丝数计算）
            '涨粉': 'followers_gain',
        }

        # 重命名列
        df.columns = [column_map.get(str(col).strip(), col) for col in df.columns]

        imported = 0
        for _, row in df.iterrows():
            try:
                title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
                if not title:
                    continue  # 跳过没有标题的行

                # 解析时间
                publish_time = parse_xiaohongshu_time(row.get('publish_time'))

                # 处理点击率（可能是小数如0.141，需要转换为百分比）
                click_rate = 0
                if pd.notna(row.get('click_rate')):
                    cr = float(row.get('click_rate', 0))
                    # 如果小于1，说明是小数形式，转为百分比
                    click_rate = cr * 100 if cr < 1 else cr

                database.add_note(
                    title=title,
                    content='',  # Excel没有文案内容
                    note_type=str(row.get('type', '图文')) if pd.notna(row.get('type')) else '图文',
                    publish_time=publish_time,
                    exposure=int(row.get('exposure', 0)) if pd.notna(row.get('exposure')) else 0,
                    views=int(row.get('views', 0)) if pd.notna(row.get('views')) else 0,
                    click_rate=click_rate,
                    likes=int(row.get('likes', 0)) if pd.notna(row.get('likes')) else 0,
                    comments=int(row.get('comments', 0)) if pd.notna(row.get('comments')) else 0,
                    saves=int(row.get('saves', 0)) if pd.notna(row.get('saves')) else 0,
                    shares=int(row.get('shares', 0)) if pd.notna(row.get('shares')) else 0,
                    followers_before=0,  # Excel没有这个数据
                    followers_after=0    # Excel没有这个数据
                )
                imported += 1
            except Exception as e:
                print(f"Error importing row: {e}")
                continue

        return jsonify({'success': True, 'imported': imported})
    except Exception as e:
        return jsonify({'error': f'导入失败：{str(e)}'}), 400


@app.route('/analysis')
def analysis():
    """AI分析页"""
    notes = database.get_all_notes()
    api_key = database.get_setting('claude_api_key')
    return render_template('analysis.html', notes=notes, has_api_key=bool(api_key))


@app.route('/api/analyze/account', methods=['POST'])
def analyze_account():
    """账号诊断分析"""
    api_key = database.get_setting('claude_api_key')
    if not api_key:
        return jsonify({'error': '请先在设置中配置 Claude API Key'}), 400

    try:
        notes = database.get_all_notes()
        overview = database.get_overview_stats()
        daily_stats = database.get_daily_stats(limit=30)
        result = ai_analyzer.analyze_account(api_key, notes, overview, daily_stats)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'分析失败：{str(e)}'}), 500


@app.route('/api/analyze/note/<int:note_id>', methods=['POST'])
def analyze_note(note_id):
    """单篇笔记分析"""
    api_key = database.get_setting('claude_api_key')
    if not api_key:
        return jsonify({'error': '请先在设置中配置 Claude API Key'}), 400

    try:
        note = database.get_note(note_id)
        if not note:
            return jsonify({'error': '笔记不存在'}), 404

        all_notes = database.get_all_notes()
        result = ai_analyzer.analyze_single_note(api_key, note, all_notes)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'分析失败：{str(e)}'}), 500


@app.route('/api/analyze/direction', methods=['POST'])
def analyze_direction():
    """内容方向建议"""
    api_key = database.get_setting('claude_api_key')
    if not api_key:
        return jsonify({'error': '请先在设置中配置 Claude API Key'}), 400

    try:
        notes = database.get_all_notes()
        overview = database.get_overview_stats()
        result = ai_analyzer.suggest_content_direction(api_key, notes, overview)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'分析失败：{str(e)}'}), 500


@app.route('/api/analyze/title', methods=['POST'])
def analyze_title():
    """标题优化"""
    api_key = database.get_setting('claude_api_key')
    if not api_key:
        return jsonify({'error': '请先在设置中配置 Claude API Key'}), 400

    try:
        data = request.json
        content = data.get('content', '')
        current_title = data.get('title', '')
        notes = database.get_all_notes()
        result = ai_analyzer.optimize_title(api_key, content, current_title, notes)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'分析失败：{str(e)}'}), 500


@app.route('/api/analyze/topics', methods=['POST'])
def analyze_topics():
    """选题推荐"""
    api_key = database.get_setting('claude_api_key')
    if not api_key:
        return jsonify({'error': '请先在设置中配置 Claude API Key'}), 400

    try:
        data = request.json or {}
        niche = data.get('niche', '')
        notes = database.get_all_notes()
        result = ai_analyzer.recommend_topics(api_key, notes, niche)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'分析失败：{str(e)}'}), 500


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """设置页"""
    if request.method == 'POST':
        api_key = request.form.get('api_key', '')
        if api_key:
            database.set_setting('claude_api_key', api_key)
        return redirect(url_for('settings'))

    current_key = database.get_setting('claude_api_key')
    masked_key = ''
    if current_key:
        masked_key = current_key[:10] + '...' + current_key[-4:] if len(current_key) > 14 else '***'

    return render_template('settings.html', masked_key=masked_key, has_key=bool(current_key))


@app.route('/api/export/<format>')
def export_data(format):
    """导出数据"""
    if format == 'json':
        data = database.export_notes_json()
        return jsonify(data)
    elif format == 'csv':
        data = database.export_notes_csv()
        return data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=notes_export.csv'
        }
    else:
        return jsonify({'error': '不支持的格式'}), 400


# ============ 一键更新数据功能 ============

@app.route('/api/scrape/start', methods=['POST'])
def api_start_scrape():
    """开始抓取小红书数据"""
    if IS_VERCEL or scraper is None:
        return jsonify({'success': False, 'error': '爬虫功能仅在本地运行，请在电脑上使用'}), 400

    try:
        result = scraper.start_scrape()

        if result.get('success'):
            imported = save_scraped_data(
                result.get('notes', []),
                result.get('account_info', {})
            )
            result['imported'] = imported

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape/continue', methods=['POST'])
def api_continue_scrape():
    """登录后继续抓取"""
    if IS_VERCEL or scraper is None:
        return jsonify({'success': False, 'error': '爬虫功能仅在本地运行'}), 400

    try:
        result = scraper.finish_scrape()

        if result.get('success'):
            imported = save_scraped_data(
                result.get('notes', []),
                result.get('account_info', {})
            )
            result['imported'] = imported

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape/cancel', methods=['POST'])
def cancel_scrape():
    """取消抓取"""
    if IS_VERCEL or scraper is None:
        return jsonify({'success': True})

    try:
        scraper.close_browser()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    database.init_db()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
