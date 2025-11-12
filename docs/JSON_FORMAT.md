# JSON 数据格式说明

## 概述

TrendRadar 从 v3.1.0 开始支持将新闻数据导出为 JSON 格式,便于后续的数据处理和 HTML 渲染。JSON 文件与 TXT 报告同步生成,存储在相同的日期目录下。

## 文件组织结构

```
output/
└── 2025年11月12日/
    ├── txt/                          # 文本报告
    │   ├── 当日汇总.txt
    │   └── 15时35分.txt
    └── json/                         # JSON 报告(新增)
        ├── news_summary.json         # 汇总文件(追加模式)
        └── news_incremental.json     # 增量文件(覆写模式)
```

## 文件类型

### 1. 汇总文件 (news_summary.json)

**作用**: 包含当天所有批次的历史数据,每次执行时追加新批次。

**更新策略**: 追加模式 - 保留历史批次,追加新批次到 `batches` 数组。

**用途**:
- 查看当天所有批次的完整历史
- 分析新闻热度随时间的变化
- 统计当天总新闻数和批次数

### 2. 增量文件 (news_incremental.json)

**作用**: 仅包含当前批次的新增数据。

**更新策略**: 覆写模式 - 每次执行时完全覆写,只保留最新批次的新增新闻。

**用途**:
- 获取最新一批新增的新闻
- 实时监控热点变化
- 推送通知和即时展示

## 数据结构详解

### 汇总文件结构 (news_summary.json)

```json
{
  "metadata": {
    "date": "2025-11-12",              // 日期 (YYYY-MM-DD)
    "total_batches": 5,                // 总批次数
    "total_news_count": 150,           // 总新闻数(所有批次累计)
    "last_update": "2025-11-12T15:35:00+08:00"  // 最后更新时间(ISO 8601格式)
  },
  "batches": [                         // 批次数组(按时间顺序)
    {
      "batch_id": "15时35分",          // 批次ID(时间标识)
      "timestamp": "2025-11-12T15:35:00+08:00",  // 批次时间戳
      "total_news_count": 28,          // 本批次新闻总数
      "stats": [                       // 词组统计数组
        {
          "word_group": "中国 美国 经济",  // 词组关键字
          "count": 15,                 // 匹配的新闻数量
          "percentage": 53.57,         // 占本批次总新闻的百分比
          "news_list": [               // 新闻列表
            {
              "title": "美就业疲软提振降息预期...",
              "url": "https://...",    // 桌面端链接
              "mobile_url": "https://m...",  // 移动端链接
              "platform": "华尔街见闻",   // 平台显示名称
              "rank": 1,               // 最高排名
              "ranks": [1, 2],         // 所有排名记录
              "occurrence_count": 2,   // 出现次数
              "time_display": "15时35分",  // 时间显示
              "is_new": false          // 是否为新增新闻
            }
          ]
        }
      ]
    }
  ]
}
```

### 增量文件结构 (news_incremental.json)

```json
{
  "metadata": {
    "date": "2025-11-12",              // 日期
    "batch_id": "15时35分",            // 当前批次ID
    "timestamp": "2025-11-12T15:35:00+08:00",  // 批次时间戳
    "new_news_count": 12               // 新增新闻总数
  },
  "stats": [                           // 词组统计数组(仅包含新增新闻)
    {
      "word_group": "中国 美国",
      "count": 5,                      // 本词组的新增新闻数
      "percentage": 41.67,             // 占新增新闻总数的百分比
      "news_list": [
        {
          "title": "...",
          "url": "https://...",
          "mobile_url": "https://m...",
          "platform": "...",
          "rank": 1,
          "ranks": [1],
          "occurrence_count": 1,
          "time_display": "15时35分"
          // 注意: 增量文件中没有 is_new 字段(都是新增)
        }
      ]
    }
  ]
}
```

## 字段说明

### 元数据字段 (metadata)

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 日期,格式: YYYY-MM-DD |
| `batch_id` | string | 批次标识,格式: "HH时MM分" |
| `timestamp` | string | ISO 8601 时间戳 |
| `total_batches` | integer | 总批次数(仅汇总文件) |
| `total_news_count` | integer | 总新闻数 |
| `new_news_count` | integer | 新增新闻数(仅增量文件) |
| `last_update` | string | 最后更新时间(仅汇总文件) |

### 批次字段 (batch)

| 字段 | 类型 | 说明 |
|------|------|------|
| `batch_id` | string | 批次标识 |
| `timestamp` | string | 批次时间戳 |
| `total_news_count` | integer | 本批次新闻总数 |
| `stats` | array | 词组统计数组 |

### 词组统计字段 (stat)

| 字段 | 类型 | 说明 |
|------|------|------|
| `word_group` | string | 词组关键字(空格分隔) |
| `count` | integer | 匹配的新闻数量 |
| `percentage` | float | 占总新闻的百分比(保留2位小数) |
| `news_list` | array | 新闻对象数组 |

### 新闻字段 (news)

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 新闻标题 |
| `url` | string | 新闻链接(桌面端) |
| `mobile_url` | string | 移动端链接 |
| `platform` | string | 平台显示名称(如 "知乎", "微博") |
| `rank` | integer | 最高排名 |
| `ranks` | array | 所有排名记录 |
| `occurrence_count` | integer | 出现次数 |
| `time_display` | string | 时间显示(如 "15时35分") |
| `is_new` | boolean | 是否为新增新闻(仅汇总文件) |

## 使用示例

### Python 读取示例

```python
import json
from pathlib import Path

# 读取汇总文件
summary_path = Path("output/2025年11月12日/json/news_summary.json")
with open(summary_path, "r", encoding="utf-8") as f:
    summary_data = json.load(f)

# 获取所有批次
batches = summary_data["batches"]
print(f"共有 {len(batches)} 个批次")

# 遍历批次
for batch in batches:
    batch_id = batch["batch_id"]
    news_count = batch["total_news_count"]
    print(f"批次 {batch_id}: {news_count} 条新闻")

    # 遍历词组
    for stat in batch["stats"]:
        word_group = stat["word_group"]
        count = stat["count"]
        print(f"  词组 '{word_group}': {count} 条")

        # 遍历新闻
        for news in stat["news_list"]:
            title = news["title"]
            rank = news["rank"]
            print(f"    - [{rank}] {title}")
```

### JavaScript 读取示例

```javascript
// 使用 fetch API 读取 JSON
fetch('output/2025年11月12日/json/news_summary.json')
  .then(response => response.json())
  .then(data => {
    const { metadata, batches } = data;

    console.log(`日期: ${metadata.date}`);
    console.log(`总批次数: ${metadata.total_batches}`);

    // 遍历批次
    batches.forEach(batch => {
      console.log(`批次 ${batch.batch_id}: ${batch.total_news_count} 条新闻`);

      // 遍历词组统计
      batch.stats.forEach(stat => {
        console.log(`  词组 '${stat.word_group}': ${stat.count} 条`);

        // 遍历新闻
        stat.news_list.forEach(news => {
          console.log(`    [${news.rank}] ${news.title}`);
        });
      });
    });
  });
```

## 数据特点

### 1. 按词组分组

数据按照 `frequency_words.txt` 中定义的词组进行分组,每个词组包含匹配的新闻列表。

### 2. 保留完整排名历史

每条新闻保留 `ranks` 数组,记录所有批次的排名变化。

### 3. 时间戳标准化

所有时间戳使用 ISO 8601 格式,便于解析和时区转换。

### 4. UTF-8 编码

JSON 文件使用 UTF-8 编码,`ensure_ascii=False`,支持中文和特殊字符。

### 5. 格式化输出

使用 `indent=2` 格式化输出,便于人工阅读和调试。

## 数据一致性保证

### 1. 原子写入

使用临时文件 + 原子重命名机制,防止写入失败导致数据损坏:

```python
# 先写临时文件
temp_file = ".tmp_news_summary.json"
with open(temp_file, "w") as f:
    json.dump(data, f)

# 原子重命名
os.replace(temp_file, "news_summary.json")
```

### 2. 异常处理

读取现有文件时捕获异常,损坏时自动重新初始化:

```python
try:
    with open(file_path, "r") as f:
        data = json.load(f)
except (json.JSONDecodeError, IOError):
    # 文件损坏,重新初始化
    data = init_structure()
```

### 3. 元数据自动更新

每次追加批次时自动更新元数据(总批次数、总新闻数、最后更新时间)。

## 版本兼容性

- **最低 Python 版本**: Python 3.10+ (使用 `typing.Tuple`)
- **JSON 格式版本**: 1.0 (未来可能添加 `format_version` 字段)
- **向后兼容**: 不影响现有 TXT 报告生成

## 常见问题

### Q1: 为什么汇总文件会越来越大?

汇总文件采用追加模式,包含当天所有批次的历史数据。每天会自动创建新的日期目录,不会无限增长。

### Q2: 如何只获取最新的新增数据?

读取 `news_incremental.json` 文件即可,它只包含最新一批的新增新闻。

### Q3: 增量文件为什么只包含新增新闻?

增量文件专门用于实时通知和即时展示,只保留本批次新增的内容,减少数据冗余。

### Q4: 如何解析时间戳?

Python 示例:
```python
from datetime import datetime
timestamp = datetime.fromisoformat(data["timestamp"])
```

JavaScript 示例:
```javascript
const timestamp = new Date(data.timestamp);
```

### Q5: 如何自定义 JSON 格式?

可以修改 `src/core/reporter.py` 中的以下方法:
- `_build_batch_data()`: 修改批次数据结构
- `_save_summary_json()`: 修改汇总逻辑
- `_save_incremental_json()`: 修改增量逻辑

## 相关文档

- [README.md](../README.md): 项目主文档
- [CLAUDE.md](../CLAUDE.md): 项目架构和开发指南
- [config/config.yaml](../config/config.yaml): 配置文件说明

## 更新日志

- **v3.1.0** (2025-11-12): 初始版本,支持汇总和增量 JSON 导出
