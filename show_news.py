# coding=utf-8
"""查看爬取到的新闻标题"""

import requests
import time

# NewNow API 地址
API_BASE = "https://newsnow.busiyi.world/api/s"

# HTTP Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

# 配置的平台列表
platforms = [
    "toutiao", "baidu", "wallstreetcn-hot", "thepaper",
    "bilibili-hot-search", "cls-hot", "ifeng", "tieba",
    "weibo", "douyin", "zhihu", "jin10"
]

print("=" * 80)
print("开始爬取各平台新闻...")
print("=" * 80)

all_news = []
for platform in platforms:
    try:
        url = f"{API_BASE}?id={platform}&latest"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        if data.get("status") in ["success", "cache"]:
            news_list = data.get("items", [])
            all_news.extend(news_list)
            print(f"✓ {platform}: {len(news_list)} 条")
        else:
            print(f"✗ {platform}: 状态={data.get('status')}")
    except Exception as e:
        print(f"✗ {platform}: {e}")

    time.sleep(0.1)  # 避免请求过快

print("\n" + "=" * 80)
print(f"总共爬取 {len(all_news)} 条新闻")
print("=" * 80)

# 显示前 50 条新闻
print("\n【前 50 条新闻标题】:\n")
for i, news in enumerate(all_news[:50], 1):
    title = news.get("title", "无标题")
    print(f"{i:2d}. {title}")

# 搜索关键词
print("\n" + "=" * 80)
keyword = "张杰"
print(f"搜索关键词: {keyword}")
print("=" * 80)

matched = []
for news in all_news:
    title = news.get("title", "")
    if keyword in title:
        matched.append(title)

print(f"\n找到 {len(matched)} 条包含 '{keyword}' 的新闻:")
if matched:
    for i, title in enumerate(matched, 1):
        print(f"{i}. {title}")
else:
    print("(无匹配)")

# 测试其他常见关键词
print("\n" + "=" * 80)
print("其他关键词统计:")
print("=" * 80)
test_keywords = ["中国", "美国", "经济", "科技", "政策", "黄金", "特朗普", "AI", "iPhone"]
for kw in test_keywords:
    count = sum(1 for news in all_news if kw in news.get("title", ""))
    print(f"  {kw}: {count} 条")
