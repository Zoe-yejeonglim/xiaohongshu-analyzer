import json
from anthropic import Anthropic


def get_client(api_key):
    """Create Anthropic client with given API key."""
    return Anthropic(api_key=api_key)


def analyze_account(api_key, notes_data, overview, daily_stats):
    """分析账号整体情况，聚焦涨粉"""
    client = get_client(api_key)

    # 计算涨粉数据
    follower_growth = []
    if daily_stats and len(daily_stats) > 1:
        for i in range(len(daily_stats) - 1):
            growth = daily_stats[i]['followers'] - daily_stats[i + 1]['followers']
            follower_growth.append({
                'date': daily_stats[i]['date'],
                'growth': growth
            })

    # 分析每篇笔记的涨粉效果
    notes_with_gain = []
    for note in notes_data:
        gain = (note.get('followers_after', 0) or 0) - (note.get('followers_before', 0) or 0)
        if gain != 0:
            notes_with_gain.append({
                'title': note.get('title', ''),
                'type': note.get('type', ''),
                'gain': gain,
                'likes': note.get('likes', 0),
                'saves': note.get('saves', 0)
            })

    # 按涨粉排序
    notes_with_gain.sort(key=lambda x: x['gain'], reverse=True)

    prompt = f"""你是一位专注于帮助博主涨粉的小红书运营专家。

**账号当前状态**：
- 粉丝数：{overview.get('followers', 0)}
- 总笔记数：{overview.get('total_notes', 0)}
- 总点赞：{overview.get('likes', 0)}
- 总收藏：{overview.get('saves', 0)}

**最近涨粉趋势**：
{json.dumps(follower_growth[:10], ensure_ascii=False, indent=2) if follower_growth else '暂无数据'}

**各笔记涨粉效果**（按涨粉数排序）：
{json.dumps(notes_with_gain[:15], ensure_ascii=False, indent=2) if notes_with_gain else '暂无数据'}

请从"如何涨粉"的角度分析：

1. **涨粉效率评估**：
   - 当前的涨粉速度如何？
   - 点赞转粉率怎么样？（有多少点赞能转化为粉丝）

2. **爆款规律总结**：
   - 涨粉最好的笔记有什么共同特点？
   - 哪种类型（图文/视频）涨粉效果更好？

3. **问题诊断**：
   - 涨粉慢的主要原因是什么？
   - 有哪些明显的问题需要改进？

4. **涨粉策略建议**：
   - 给出3-5条具体可执行的涨粉建议
   - 按优先级排序，最重要的放前面

请用简洁、直接的语言回答，重点突出可执行的建议。"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def analyze_single_note(api_key, note_data, all_notes_data):
    """分析单篇笔记的涨粉效果"""
    client = get_client(api_key)

    # 计算这篇笔记的涨粉
    gain = (note_data.get('followers_after', 0) or 0) - (note_data.get('followers_before', 0) or 0)

    # 计算平均数据
    if all_notes_data:
        gains = [(n.get('followers_after', 0) or 0) - (n.get('followers_before', 0) or 0) for n in all_notes_data]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_likes = sum(n.get('likes', 0) for n in all_notes_data) / len(all_notes_data)
    else:
        avg_gain = avg_likes = 0

    prompt = f"""你是一位小红书涨粉专家。

**这篇笔记的数据**：
- 标题：{note_data.get('title', '')}
- 内容：{note_data.get('content', '（未填写）')}
- 类型：{note_data.get('type', '未知')}
- 曝光：{note_data.get('exposure', 0)}
- 点赞：{note_data.get('likes', 0)}（账号平均：{avg_likes:.0f}）
- 收藏：{note_data.get('saves', 0)}
- 评论：{note_data.get('comments', 0)}
- **涨粉：{gain}**（账号平均：{avg_gain:.1f}）

请分析：

1. **涨粉效果评价**：
   - 这篇笔记涨粉效果如何？（好/一般/差）
   - 和账号平均水平相比如何？

2. **原因分析**：
   - 为什么这篇笔记涨粉{('效果好' if gain > avg_gain else '效果一般')}？
   - 点赞转粉率如何？

3. **标题分析**：
   - 标题是否有吸引力？
   - 标题是否能吸引目标粉丝？

4. **改进建议**：
   - 如果重新发这个选题，应该怎么优化？
   - 给出2-3条具体建议"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def suggest_content_direction(api_key, notes_data, overview):
    """建议内容方向，聚焦涨粉"""
    client = get_client(api_key)

    # 按涨粉效果排序笔记
    notes_with_gain = []
    for note in notes_data:
        gain = (note.get('followers_after', 0) or 0) - (note.get('followers_before', 0) or 0)
        notes_with_gain.append({
            'title': note.get('title', ''),
            'type': note.get('type', ''),
            'gain': gain,
            'likes': note.get('likes', 0)
        })

    notes_with_gain.sort(key=lambda x: x['gain'], reverse=True)
    top_notes = notes_with_gain[:5]
    bottom_notes = notes_with_gain[-5:] if len(notes_with_gain) > 5 else []

    prompt = f"""你是一位小红书内容策略专家，专注于帮助博主涨粉。

**账号状态**：
- 当前粉丝：{overview.get('followers', 0)}

**涨粉最好的5篇笔记**：
{json.dumps(top_notes, ensure_ascii=False, indent=2)}

**涨粉最差的5篇笔记**：
{json.dumps(bottom_notes, ensure_ascii=False, indent=2)}

请分析并给出建议：

1. **涨粉规律总结**：
   - 涨粉好的内容有什么共同点？
   - 涨粉差的内容有什么问题？

2. **内容方向建议**：
   - 应该主攻什么类型的内容？
   - 图文和视频哪个更适合涨粉？

3. **5个涨粉选题推荐**：
   - 基于分析，推荐5个可能涨粉的选题
   - 每个选题说明为什么可能涨粉

4. **避坑建议**：
   - 哪些类型的内容应该避免？"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def optimize_title(api_key, content, current_title, notes_data):
    """优化标题，提升点击和涨粉"""
    client = get_client(api_key)

    # 获取涨粉最好的标题作为参考
    notes_with_gain = []
    for note in notes_data:
        gain = (note.get('followers_after', 0) or 0) - (note.get('followers_before', 0) or 0)
        if note.get('title') and gain > 0:
            notes_with_gain.append({
                'title': note.get('title'),
                'gain': gain
            })

    notes_with_gain.sort(key=lambda x: x['gain'], reverse=True)
    top_titles = [n['title'] for n in notes_with_gain[:5]]

    prompt = f"""你是一位小红书爆款标题专家。

**笔记内容**：
{content if content else '（未提供）'}

**当前标题**：
{current_title if current_title else '（未提供）'}

**这个账号涨粉最好的标题**：
{chr(10).join(['- ' + t for t in top_titles]) if top_titles else '暂无数据'}

请：
1. **分析当前标题**（如有）的问题
2. **提供5个优化标题**，要求：
   - 能吸引点击
   - 能吸引精准粉丝（不是泛流量）
   - 控制在20字以内
   - 使用不同技巧（数字、悬念、痛点、共鸣等）

格式：
**标题1**：xxx
技巧：xxx | 预期效果：xxx

**标题2**：xxx
技巧：xxx | 预期效果：xxx

...以此类推"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def recommend_topics(api_key, notes_data, user_niche=""):
    """推荐可能涨粉的选题"""
    client = get_client(api_key)

    # 分析已发内容
    existing_titles = [n.get('title', '') for n in notes_data if n.get('title')]

    # 涨粉效果分析
    notes_with_gain = []
    for note in notes_data:
        gain = (note.get('followers_after', 0) or 0) - (note.get('followers_before', 0) or 0)
        notes_with_gain.append({
            'title': note.get('title', ''),
            'gain': gain
        })

    notes_with_gain.sort(key=lambda x: x['gain'], reverse=True)

    prompt = f"""你是一位小红书选题专家，专注于帮助博主涨粉。

**账号领域**：
{user_niche if user_niche else '（请根据内容推断）'}

**已发布的笔记标题**：
{chr(10).join(['- ' + t for t in existing_titles[:15]]) if existing_titles else '暂无'}

**涨粉效果排名**（前5）：
{json.dumps(notes_with_gain[:5], ensure_ascii=False, indent=2) if notes_with_gain else '暂无'}

请推荐选题：

1. **账号定位分析**：
   - 这个账号的目标粉丝是谁？
   - 粉丝关注这个账号是为了获得什么？

2. **10个涨粉选题推荐**：
   每个选题包含：
   - 具体标题
   - 内容要点（2-3点）
   - 为什么可能涨粉
   - 适合图文还是视频

3. **系列内容建议**：
   - 推荐1-2个可以做成系列的选题
   - 系列内容更容易涨粉

请确保选题具体、可执行，不要太泛泛。"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1800,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
