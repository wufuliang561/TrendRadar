# TrendRadar 重构版使用说明

## 项目概述

本项目已完成从单文件（4000+ 行）到模块化架构的重构。新架构采用分层设计，具有更好的可维护性和可扩展性。

## 新架构说明

### 目录结构

```
src/
├── models/          # 数据模型
│   └── news.py     # News, NewsStatistic, WordGroupStatistic
├── core/            # 核心业务逻辑
│   ├── config.py   # 配置管理
│   ├── filter.py   # 关键词筛选
│   ├── ranking.py  # 权重计算和排序
│   ├── reporter.py # 报告生成
│   └── push_record.py  # 推送记录管理
├── sources/         # 信息源（可扩展）
│   ├── base.py     # 信息源抽象基类
│   ├── newsnow.py  # NewNow热榜聚合
│   ├── rss.py      # RSS订阅源
│   └── registry.py # 信息源注册器
├── notifiers/       # 通知渠道（可扩展）
│   ├── base.py     # 通知器抽象基类
│   ├── batch_sender.py  # 分批发送工具
│   ├── manager.py  # 通知管理器
│   ├── feishu.py   # 飞书
│   ├── dingtalk.py # 钉钉
│   ├── wework.py   # 企业微信
│   ├── telegram.py # Telegram
│   ├── email.py    # 邮件
│   └── ntfy.py     # ntfy
├── utils/           # 工具函数
│   ├── time.py     # 时间处理
│   ├── file.py     # 文件操作
│   └── http.py     # HTTP客户端
└── app.py           # 主应用类

main.py          # 新的入口文件
main_legacy.py       # 原始代码（备份）
```

### 核心设计原则

1. **单一职责**：每个模块只负责一个功能
2. **开放封闭**：易于扩展，无需修改核心代码
3. **依赖倒置**：面向接口编程，使用抽象基类
4. **插件化**：信息源和通知渠道均可插件式扩展

## 快速开始

### 基本用法

```bash
# 使用默认配置运行（daily模式）
python3 main.py

# 指定运行模式
python3 main.py --mode current      # 当前榜单
python3 main.py --mode incremental  # 增量监控

# 使用自定义配置
python3 main.py --config my_config.yaml
```

### 查看状态

```bash
# 列出所有信息源
python3 main.py --list-sources

# 列出所有通知渠道配置状态
python3 main.py --list-notifiers

# 显示配置摘要
python3 main.py --show-config
```

## 运行模式

### 1. daily（当日汇总）
- 汇总当天所有匹配的新闻
- 适合定时推送每日报告
- 包含历史统计信息（出现次数、时间范围）

### 2. current（当前榜单）
- 只推送当前批次的新闻
- 适合高频监控
- 仍然保留历史统计信息

### 3. incremental（增量监控）
- 只推送新增的新闻
- 适合实时监控
- 隐藏新增新闻区域（避免重复）

## 扩展指南

### 添加新的信息源

1. 创建新类继承 `BaseSource`
2. 实现必需方法：`source_id`, `source_name`, `fetch_news()`
3. 在 `sources/registry.py` 中注册

示例：
```python
from src.sources.base import BaseSource
from src.models.news import News

class MySource(BaseSource):
    @property
    def source_id(self) -> str:
        return "my_source"

    @property
    def source_name(self) -> str:
        return "我的信息源"

    def fetch_news(self, **kwargs) -> List[News]:
        # 实现爬取逻辑
        news_list = []
        # ... 爬取代码 ...
        return news_list
```

### 添加新的通知渠道

1. 创建新类继承 `BaseNotifier`
2. 实现必需方法：`name`, `is_configured()`, `send()`
3. 在 `notifiers/manager.py` 中注册

示例：
```python
from src.notifiers.base import BaseNotifier

class MyNotifier(BaseNotifier):
    @property
    def name(self) -> str:
        return "我的通知渠道"

    def is_configured(self) -> bool:
        return bool(self.config.get("MY_WEBHOOK_URL"))

    def send(self, report_data, report_type, **kwargs) -> bool:
        # 实现发送逻辑
        # ...
        return True
```

## 测试

项目包含全面的单元测试（87个测试用例）：

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定模块测试
python3 -m pytest tests/test_core/ -v
python3 -m pytest tests/test_sources/ -v

# 查看测试覆盖率
python3 -m pytest tests/ --cov=src --cov-report=html
```

## 配置说明

### 环境变量优先级

配置项优先级：**环境变量 > config.yaml**

示例：
```bash
# 环境变量会覆盖配置文件
export FEISHU_WEBHOOK_URL="https://..."
python3 main.py
```

### 关键配置项

#### 信息源配置
```yaml
SOURCES:
  enabled:
    - newsnow
    - rss  # 如需启用RSS
  newsnow:
    platforms:
      - id: zhihu
        name: 知乎
      # ...
```

#### 通知配置
```yaml
# 飞书
FEISHU_WEBHOOK_URL: ""  # 从环境变量读取

# 钉钉
DINGTALK_WEBHOOK_URL: ""

# 企业微信
WEWORK_WEBHOOK_URL: ""

# Telegram
TELEGRAM_BOT_TOKEN: ""
TELEGRAM_CHAT_ID: ""

# 邮件
EMAIL_FROM: ""
EMAIL_PASSWORD: ""
EMAIL_TO: ""

# ntfy
NTFY_SERVER_URL: "https://ntfy.sh"
NTFY_TOPIC: ""
```

#### 推送窗口控制
```yaml
PUSH_WINDOW:
  ENABLED: true
  TIME_RANGE:
    START: "09:00"
    END: "18:00"
  ONCE_PER_DAY: true
  RECORD_RETENTION_DAYS: 7
```

## 与原版本的区别

### 优势

✅ **模块化设计**：代码按功能分层，易于理解和维护
✅ **可扩展性**：插件式架构，添加新功能无需修改核心代码
✅ **可测试性**：每个模块都有独立的单元测试
✅ **类型安全**：使用类型提示，减少运行时错误
✅ **统一接口**：所有信息源和通知器使用统一的接口
✅ **配置灵活**：支持环境变量覆盖，适合CI/CD
✅ **错误处理**：完善的异常捕获和日志输出

### 兼容性

✅ **配置文件**：完全兼容原版 config.yaml
✅ **输出格式**：文本报告格式与原版一致
✅ **推送逻辑**：保留所有推送控制功能
✅ **数据格式**：输出目录结构与原版相同

### 迁移建议

1. **保留原版**：`main.py` 已备份为 `main_legacy.py`
2. **测试新版**：先用 `main.py` 测试功能
3. **对比输出**：比较两个版本的输出是否一致
4. **逐步迁移**：确认无误后替换主入口

## 常见问题

### Q: 如何回退到原版本？
A: 直接运行 `python3 main_legacy.py` 即可。

### Q: 新版本性能如何？
A: 模块化设计对性能影响极小，核心算法保持一致。

### Q: 如何调试问题？
A: 每个模块都有详细的日志输出，可以追踪完整流程。

### Q: 是否支持Docker部署？
A: 是的，使用方式与原版相同，只需将 `main.py` 改为 `main.py`。

## 贡献指南

欢迎贡献新的信息源或通知渠道！

1. Fork 项目
2. 创建新的信息源/通知器类
3. 编写测试用例
4. 提交 Pull Request

## 技术栈

- Python 3.10+
- requests (HTTP请求)
- PyYAML (配置管理)
- feedparser (RSS解析)
- pytz (时区处理)
- pytest (测试框架)

## 许可证

与原项目保持一致。
