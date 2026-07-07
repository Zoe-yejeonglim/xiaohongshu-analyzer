# 小红书运营分析工具

个人小红书账号数据分析和管理工具。

## 功能

- **数据概览**: 粉丝趋势图、每日数据记录
- **笔记管理**: 查看所有笔记的曝光、点赞、收藏等数据
- **一键更新**: 自动从小红书创作者中心抓取最新数据
- **AI分析**: 使用Claude API进行账号诊断和内容建议
- **数据导入**: 支持从Excel导入笔记数据

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

## 运行

```bash
python app.py
```

访问 http://localhost:5000

## 数据同步

数据存储在 `data/` 目录下。如需多设备同步，修改 `config.py` 中的 `DATA_DIR` 指向iCloud文件夹：

```python
DATA_DIR = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/xiaohongshu-data"
```

## 技术栈

- Flask (Web框架)
- SQLite (数据库)
- Playwright (网页自动化)
- Chart.js (图表)
- Claude API (AI分析)
