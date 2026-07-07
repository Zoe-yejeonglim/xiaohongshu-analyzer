"""
小红书数据抓取模块
"""

from playwright.sync_api import sync_playwright
import re
import time
import config

USER_DATA_DIR = str(config.BROWSER_DATA_DIR)

_pending_context = None
_pending_page = None


def start_scrape():
    """一键抓取"""
    global _pending_context, _pending_page
    config.init_dirs()

    result = {
        'success': False,
        'notes': [],
        'account_info': {},
        'error': None
    }

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()

        context = playwright.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.on('dialog', lambda d: d.dismiss())

        # 1. 访问创作者中心首页
        print("访问小红书创作者中心首页...")
        page.goto('https://creator.xiaohongshu.com/creator/home', wait_until='domcontentloaded', timeout=30000)
        time.sleep(5)  # 等待页面渲染
        handle_popups(page)

        # 检查登录状态
        if 'login' in page.url.lower() or page.locator('text=扫码登录').count() > 0:
            result['error'] = 'NEED_LOGIN'
            result['message'] = '请在浏览器中扫码登录，登录后点击"继续抓取"'
            _pending_context = context
            _pending_page = page
            return result

        # 2. 从首页抓取账号总体数据
        print("抓取首页账号数据...")
        account_info = scrape_home_page(page)
        result['account_info'] = account_info
        print(f"  粉丝: {account_info.get('followers', 0)}, 获赞与收藏: {account_info.get('likes_and_saves', 0)}")

        # 3. 点击侧边栏的笔记管理菜单
        print("点击笔记管理菜单...")
        note_manage = page.locator('[class*="menu"] >> text=笔记管理')
        if note_manage.count() > 0:
            note_manage.click()
            time.sleep(3)
            handle_popups(page)
            print(f"  导航到: {page.url}")
        else:
            print("  未找到笔记管理菜单")

        # 4. 等待笔记管理页面加载
        print("等待笔记列表加载...")
        time.sleep(2)

        # 5. 抓取笔记列表数据
        print("抓取笔记数据...")
        notes = scrape_notes_list(page)
        result['notes'] = notes

        result['success'] = True
        result['message'] = f'成功抓取账号数据和 {len(notes)} 篇笔记'
        print(f"完成！共抓取 {len(notes)} 篇笔记")

    except Exception as e:
        result['error'] = str(e)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if context and result.get('success'):
            try:
                context.close()
            except:
                pass

    return result


def finish_scrape():
    """登录后继续"""
    global _pending_context, _pending_page

    if not _pending_context or not _pending_page:
        return {'success': False, 'error': '没有待处理的会话'}

    result = {
        'success': False,
        'notes': [],
        'account_info': {},
        'error': None
    }

    page = _pending_page
    context = _pending_context

    try:
        time.sleep(2)
        page.reload()
        time.sleep(3)
        handle_popups(page)

        if 'login' in page.url.lower():
            return {'success': False, 'error': '请先完成登录'}

        # 抓取首页数据
        account_info = scrape_home_page(page)
        result['account_info'] = account_info

        # 点击侧边栏的笔记管理菜单
        note_manage = page.locator('[class*="menu"] >> text=笔记管理')
        if note_manage.count() > 0:
            note_manage.click()
            time.sleep(3)
            handle_popups(page)

        # 抓取笔记
        notes = scrape_notes_list(page)
        result['notes'] = notes
        result['success'] = True
        result['message'] = f'成功抓取 {len(notes)} 篇笔记'

    except Exception as e:
        result['error'] = str(e)

    finally:
        try:
            context.close()
        except:
            pass
        _pending_context = None
        _pending_page = None

    return result


def handle_popups(page):
    """关闭弹窗"""
    for _ in range(3):
        try:
            for text in ['屏蔽', '拒绝', '取消', '关闭', '我知道了', '暂不', '稍后']:
                btn = page.locator(f'button:has-text("{text}"):visible').first
                if btn.count() > 0:
                    btn.click()
                    time.sleep(0.3)
        except:
            pass


def scrape_home_page(page):
    """从首页抓取账号数据"""
    info = {'followers': 0, 'likes_and_saves': 0}

    try:
        # 获取整个页面文本
        text = page.inner_text('body')

        # 方法1: 直接匹配 "1002 粉丝数" 格式
        fans_match = re.search(r'(\d+(?:,\d+)*)\s*粉丝数', text)
        if fans_match:
            info['followers'] = int(fans_match.group(1).replace(',', ''))

        # 方法2: 匹配 "粉丝数 1002" 格式
        if info['followers'] == 0:
            fans_match = re.search(r'粉丝数\s*(\d+(?:,\d+)*)', text)
            if fans_match:
                info['followers'] = int(fans_match.group(1).replace(',', ''))

        # 获赞与收藏
        likes_match = re.search(r'(\d+(?:,\d+)*)\s*获赞与收藏', text)
        if likes_match:
            info['likes_and_saves'] = int(likes_match.group(1).replace(',', ''))

        if info['likes_and_saves'] == 0:
            likes_match = re.search(r'获赞与收藏\s*(\d+(?:,\d+)*)', text)
            if likes_match:
                info['likes_and_saves'] = int(likes_match.group(1).replace(',', ''))

    except Exception as e:
        print(f"抓取首页数据失败: {e}")

    return info


def scrape_notes_list(page):
    """从笔记管理页面抓取笔记列表"""
    notes = []

    # 等待加载
    time.sleep(2)

    # 滚动加载所有笔记 - 滚动.content容器而不是body
    print("  滚动加载...")
    last_count = 0
    no_change_count = 0
    for i in range(200):  # 最多滚动200次
        # 滚动.content容器
        page.evaluate('''() => {
            const container = document.querySelector(".content");
            if (container) {
                container.scrollTop = container.scrollHeight;
            } else {
                window.scrollTo(0, document.body.scrollHeight);
            }
        }''')
        time.sleep(0.6)  # 增加等待时间让内容加载
        current_height = page.evaluate('''() => {
            const container = document.querySelector(".content");
            return container ? container.scrollHeight : document.body.scrollHeight;
        }''')
        if current_height == last_count:
            no_change_count += 1
            if no_change_count >= 8:  # 连续8次没变化才停止
                break
            time.sleep(0.5)  # 额外等待
        else:
            no_change_count = 0
        last_count = current_height
        if i % 20 == 0:
            print(f"    滚动第{i+1}次，高度: {current_height}")

    # 回到顶部
    page.evaluate('''() => {
        const container = document.querySelector(".content");
        if (container) container.scrollTop = 0;
        window.scrollTo(0, 0);
    }''')
    time.sleep(1)

    print("  解析笔记数据...")

    # 获取页面全部文本
    page_text = page.inner_text('body')
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]

    # 解析逻辑：找日期行，然后前面是标题，后面是数据
    # 格式：标题 -> 日期 -> 曝光 -> 点击率 -> 点赞 -> 收藏 -> 评论
    i = 0
    while i < len(lines):
        line = lines[i]
        # 匹配日期格式: 2025-10-10 17:51 或 2026-06-26 17:25
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})$', line)
        if date_match and i > 0:
            # 找到日期，往前找标题
            title = None
            for j in range(i-1, max(i-5, -1), -1):
                candidate = lines[j]
                # 跳过置顶、视频时长等标记
                if candidate in ['置顶', '仅自己可见', '审核中', '未通过'] or re.match(r'^\d{2}:\d{2}$', candidate):
                    continue
                # 跳过纯数字
                if re.match(r'^[\d,]+$', candidate):
                    continue
                # 找到有效标题
                if len(candidate) >= 3 and len(candidate) <= 100:
                    title = candidate
                    break

            if title:
                note = {
                    'title': title,
                    'type': '图文',
                    'publish_time': date_match.group(1),
                    'exposure': 0,
                    'views': 0,
                    'click_rate': 0,
                    'likes': 0,
                    'comments': 0,
                    'saves': 0,
                    'shares': 0
                }

                # 检查是否有视频时长标记
                for j in range(i-1, max(i-3, -1), -1):
                    if re.match(r'^\d{2}:\d{2}$', lines[j]):
                        note['type'] = '视频'
                        break

                # 读取日期后面的数字数据
                nums = []
                for k in range(i+1, min(i+8, len(lines))):
                    num_line = lines[k]
                    # 匹配数字（可能有逗号）
                    num_match = re.match(r'^([\d,]+)$', num_line)
                    if num_match:
                        nums.append(int(num_match.group(1).replace(',', '')))
                    # 如果遇到下一个日期或标题，停止
                    elif re.match(r'^\d{4}-\d{2}-\d{2}', num_line) or len(num_line) > 20:
                        break

                # 分配数据：曝光、点击率、点赞、收藏、评论
                if len(nums) >= 1:
                    note['exposure'] = nums[0]
                if len(nums) >= 2:
                    note['click_rate'] = nums[1]
                if len(nums) >= 3:
                    note['likes'] = nums[2]
                if len(nums) >= 4:
                    note['saves'] = nums[3]
                if len(nums) >= 5:
                    note['comments'] = nums[4]

                notes.append(note)

        i += 1

    print(f"  共解析 {len(notes)} 篇笔记")
    return notes


def parse_note_row(text):
    """解析笔记行文本"""
    if not text or len(text.strip()) < 5:
        return None

    note = {
        'title': '',
        'type': '图文',
        'exposure': 0,
        'views': 0,
        'click_rate': 0,
        'likes': 0,
        'comments': 0,
        'saves': 0,
        'shares': 0
    }

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # 跳过表头
    if '笔记标题' in text or '曝光数' in text and '观看数' in text:
        return None

    # 找标题
    skip = ['图文', '视频', '编辑', '删除', '查看数据', '更多', '已发布', '审核中', '未通过']
    for line in lines:
        # 跳过纯数字行
        if re.match(r'^[\d,.\s%\-]+$', line):
            continue
        # 跳过太短或太长
        if len(line) < 3 or len(line) > 100:
            continue
        # 跳过关键词
        if line in skip:
            continue
        # 跳过包含特定模式的
        if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}', line):  # 日期
            continue

        note['title'] = line
        break

    if not note['title']:
        return None

    # 类型
    if '视频' in text:
        note['type'] = '视频'

    # 提取数字
    numbers = re.findall(r'(\d+(?:,\d+)*)', text)
    nums = []
    for n in numbers:
        try:
            nums.append(int(n.replace(',', '')))
        except:
            pass

    # 过滤掉太大的数字（可能是ID）和太小的数字
    nums = [n for n in nums if 0 <= n <= 10000000]

    # 分配数据（假设顺序：曝光、观看、点赞、收藏、评论）
    if len(nums) >= 1:
        note['exposure'] = nums[0]
    if len(nums) >= 2:
        note['views'] = nums[1]
    if len(nums) >= 3:
        note['likes'] = nums[2]
    if len(nums) >= 4:
        note['saves'] = nums[3]
    if len(nums) >= 5:
        note['comments'] = nums[4]

    # 点击率
    rate = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    if rate:
        note['click_rate'] = float(rate.group(1))

    return note


def close_browser():
    """关闭浏览器"""
    global _pending_context, _pending_page
    if _pending_context:
        try:
            _pending_context.close()
        except:
            pass
    _pending_context = None
    _pending_page = None
