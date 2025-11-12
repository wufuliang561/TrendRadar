# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

TrendRadar 是一个热点新闻聚合与智能分析工具,支持从 11+ 个主流平台(知乎、微博、抖音、bilibili 等)爬取热点新闻,通过关键词筛选、权重算法排序后推送到多个通知渠道,并提供基于 MCP (Model Context Protocol) 的 AI 分析功能。

**技术栈**: Python 3.10+, FastMCP, PyYAML, requests, pytz, pytest

**重要**: 项目已完成重构,从单文件(main_legacy.py 4000+ 行)迁移到模块化架构(src/ 目录)。新架构采用 SOLID 原则和插件化设计。

## 核心命令

### 开发环境设置

```bash
# macOS/Linux 系统初始化
./setup-mac.sh

# Windows 系统初始化
setup-windows.bat

# 或使用英文版(Windows)
setup-windows-en.bat
```

### 主要运行命令

```bash
# 运行重构后的程序（推荐）
python main.py                    # 默认 daily 模式
python main.py --mode current     # 当前榜单模式
python main.py --mode incremental # 增量监控模式
python main.py --list-sources     # 列出所有信息源
python main.py --list-notifiers   # 列出通知渠道配置
python main.py --show-config      # 显示配置摘要

# 运行原始版本（备份）
python main_legacy.py

# 启动 MCP HTTP 服务器(用于 AI 分析)
# Windows: start-http.bat
# Mac/Linux: ./start-http.sh
# 或手动启动:
uv run python -m mcp_server.server --transport http --port 3333
```

### 测试命令

```bash
# 运行所有测试（87+ 测试用例）
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_core/ -v
pytest tests/test_sources/ -v
pytest tests/test_notifiers/ -v

# 查看测试覆盖率
pytest tests/ --cov=src --cov-report=html

# 手动触发 GitHub Actions 测试
# 访问: https://github.com/{你的用户名}/TrendRadar/actions
# 点击 "Hot News Crawler" -> "Run workflow"
```

### Docker 部署命令

```bash
# 进入 docker 目录
cd docker

# 拉取并启动服务
docker-compose pull
docker-compose up -d

# 查看日志
docker logs -f trend-radar

# 服务管理
docker exec -it trend-radar python manage.py status  # 查看状态
docker exec -it trend-radar python manage.py run     # 手动执行爬虫
docker exec -it trend-radar python manage.py logs    # 查看实时日志
docker exec -it trend-radar python manage.py config  # 显示配置
```

## 架构设计

### 整体架构（重构后）

项目采用**分层模块化架构**:

```
src/
├── models/          # 数据模型层
│   └── news.py     # News, NewsStatistic, WordGroupStatistic
├── core/            # 核心业务层
│   ├── config.py   # 配置管理 (ConfigManager)
│   ├── filter.py   # 关键词筛选 (NewsFilter)
│   ├── ranking.py  # 权重计算和排序 (NewsRanking)
│   ├── reporter.py # 报告生成 (NewsReporter)
│   └── push_record.py  # 推送记录管理 (PushRecordManager)
├── sources/         # 信息源层（插件化）
│   ├── base.py     # BaseSource 抽象基类
│   ├── newsnow.py  # NewNowSource (默认)
│   ├── rss.py      # RSSSource (扩展示例)
│   └── registry.py # SourceRegistry 注册器
├── notifiers/       # 通知层（插件化）
│   ├── base.py     # BaseNotifier 抽象基类
│   ├── manager.py  # NotificationManager
│   ├── batch_sender.py  # BatchSender 分批发送工具
│   ├── feishu.py   # 飞书
│   ├── dingtalk.py # 钉钉
│   ├── wework.py   # 企业微信
│   ├── telegram.py # Telegram
│   ├── email.py    # 邮件
│   └── ntfy.py     # ntfy
├── utils/           # 工具函数
│   ├── time.py     # 北京时间处理、格式化
│   ├── file.py     # 文件操作、HTML转义
│   └── http.py     # HTTP客户端（支持重试和代理）
└── app.py           # TrendRadarApp 主应用类

mcp_server/          # MCP 协议服务器（独立模块）
├── server.py        # FastMCP 2.0 入口
├── tools/           # 13 个 MCP 工具
├── services/        # 数据服务层
└── utils/           # MCP 工具函数

config/              # 配置文件目录
output/              # 数据输出目录（运行时生成）
tests/               # 单元测试（87+ 测试用例）

main.py              # 重构后的入口文件
main_legacy.py       # 原始单文件版本（备份）
```

### 核心工作流程

```
1. ConfigManager 加载配置（config.yaml + 环境变量）
2. SourceRegistry 初始化信息源
3. BaseSource 子类爬取新闻数据
4. NewsFilter 关键词筛选（普通词/必须词+/过滤词!）
5. NewsRanking 权重计算和排序（排名60% + 频次30% + 热度10%）
6. NewsReporter 生成报告（文本/HTML）
7. NotificationManager 多渠道推送
8. PushRecordManager 记录推送状态（时间窗口控制）
```

**关键类和方法**:
- `TrendRadarApp.run(mode)`: 主执行流程 (src/app.py:200+)
- `ConfigManager.load_config()`: 配置加载 (src/core/config.py:30+)
- `NewsFilter.filter_news()`: 关键词筛选 (src/core/filter.py:100+)
- `NewsRanking.calculate_weights()`: 权重计算 (src/core/ranking.py:150+)
- `NewsReporter.generate_report()`: 报告生成 (src/core/reporter.py:80+)
- `NotificationManager.send_notifications()`: 通知推送 (src/notifiers/manager.py:50+)

### MCP 服务器架构（AI 分析功能）

```
mcp_server/
├── server.py           # FastMCP 2.0 入口,注册所有工具
├── tools/              # 13 个 MCP 工具实现
│   ├── data_query.py   # 基础查询(最新新闻/按日期查询/热门话题)
│   ├── search_tools.py # 智能检索(搜索新闻/历史关联)
│   ├── analytics.py    # 高级分析(趋势分析/情感分析/摘要生成)
│   ├── config_mgmt.py  # 配置管理
│   └── system.py       # 系统管理(状态查询/触发爬取)
├── services/           # 业务服务层
│   ├── data_service.py   # 数据加载与聚合(读取 output/ 目录数据)
│   ├── parser_service.py # 数据解析(解析 HTML/TXT 新闻文件)
│   └── cache_service.py  # 缓存服务(减少重复文件读取)
└── utils/              # 工具函数
```

**MCP 工具分类**:
1. **基础查询**: get_latest_news, get_news_by_date, get_trending_topics
2. **智能检索**: search_news, search_related_news_history
3. **高级分析**: analyze_topic_trend, analyze_data_insights, analyze_sentiment, find_similar_news, generate_summary_report
4. **系统管理**: get_current_config, get_system_status, trigger_crawl

### 配置管理体系

**config/config.yaml** - 主配置文件:
- `app`: 版本检查设置
- `crawler`: 爬虫配置(请求间隔、代理设置)
- `report`: 推送模式(daily/current/incremental)
- `notification`: 通知配置(webhook URLs 应填入 GitHub Secrets,不要写在文件中)
- `weight`: 热度权重算法参数
- `platforms`: 监控平台列表(11 个默认平台,可扩展)

**config/frequency_words.txt** - 关键词筛选配置:
- 支持普通词、必须词(+)、过滤词(!) 三种语法
- 空行分隔不同词组,独立统计

**配置优先级**: 环境变量 > config.yaml (由 ConfigManager 统一管理)

### 数据流架构

```
newsnow API → NewNowSource.fetch_news() → NewsFilter.filter_news()
    → NewsRanking.calculate_weights() → NewsReporter.generate_report()
    → NotificationManager.send_notifications() → output/news_{date}.txt/html
    → MCP Server 读取 → AI 分析
```

### 推送模式说明

1. **daily**(当日汇总): 定时推送当日所有匹配新闻 + 新增区域
2. **current**(当前榜单): 定时推送当前榜单匹配新闻 + 新增区域
3. **incremental**(增量监控): 仅推送新增内容(有新增才推送)

可选配置**推送时间窗口**(`push_window`),限制推送时间范围(如 09:00-18:00)

## 开发注意事项

### 代码架构原则

**重要**: 项目已重构,遵循 SOLID 原则:
- **单一职责**: 每个类只负责一个功能
- **开放封闭**: 通过继承 BaseSource/BaseNotifier 扩展,无需修改核心
- **里氏替换**: 所有子类可替换基类使用
- **接口隔离**: 接口简洁明确
- **依赖倒置**: 依赖抽象基类而非具体实现

### 扩展新功能

**添加新信息源**:
1. 在 `src/sources/` 创建新文件
2. 继承 `BaseSource` 并实现 3 个方法: `source_id`, `source_name`, `fetch_news()`
3. 在 `SourceRegistry` 中注册（自动发现）

**添加新通知渠道**:
1. 在 `src/notifiers/` 创建新文件
2. 继承 `BaseNotifier` 并实现 3 个方法: `name`, `is_configured()`, `send()`
3. 在 `NotificationManager` 中注册

示例代码参考: src/sources/rss.py (RSS信息源示例)

### 测试开发

**重要**: 所有新功能必须编写单元测试
- 测试文件放在 `tests/` 目录,遵循模块结构
- 使用 pytest 框架,参考现有测试用例
- 运行 `pytest tests/ -v` 确保所有测试通过
- 当前测试覆盖: 87+ 测试用例

### 配置安全

- **禁止**在 config/config.yaml 中填写 webhook URLs
- 所有敏感信息必须通过 **GitHub Secrets** 或**环境变量**传递
- GitHub Actions 通过 `secrets.*` 注入环境变量
- Docker 通过 `.env` 文件或 `-e` 参数传递
- ConfigManager 自动处理环境变量优先级

### 版本兼容性

**重要**: 项目维护两个版本
- `main.py`: 重构后版本（推荐用于开发和扩展）
- `main_legacy.py`: 原始单文件版本（向后兼容，保留备份）

**小版本升级**（用户角度）: 只需替换 main_legacy.py
**大版本升级**: 建议重新 fork,避免配置冲突

**开发建议**:
- 新功能开发基于重构后的 `src/` 架构
- 保持两个版本的输出格式一致性
- 关键算法变更需同步到两个版本

### 关键依赖管理

- 使用 `uv` 作为包管理器(setup 脚本会自动安装)
- `requirements.txt` 和 `pyproject.toml` 需同步维护
- Python 版本要求: >=3.10
- 核心依赖: requests, PyYAML, pytz, fastmcp, pytest (测试)

### 代码规范

- 所有文件使用 UTF-8 编码(无 BOM)
- 使用类型提示 (type hints) 提高代码可读性
- 公共接口必须有 docstring 注释（中文）
- 遵循 PEP 8 代码风格
- 单个文件不超过 500 行（原则）

### 定时任务配置

**GitHub Actions**:
- 修改 `.github/workflows/crawler.yml` 中的 cron 表达式
- 默认每小时执行一次: `0 * * * *`
- **不建议**设置低于 30 分钟,避免滥用 GitHub 资源

**Docker**:
- 通过 `CRON_SCHEDULE` 环境变量控制
- 默认每 5 分钟: `*/5 * * * *`

### 数据持久化

- `output/` 目录存储所有生成的新闻数据(HTML/TXT 格式)
- 文件命名: `news_{YYYY-MM-DD}.txt`, `news_{YYYY-MM-DD}.html`
- Docker 部署时挂载 `./output:/app/output` 保证数据持久化

### MCP 开发约定

- **工具注册**: 所有 MCP 工具必须在 `server.py` 中通过 `@mcp.tool` 装饰器注册
- **参数验证**: 工具函数需进行参数校验,返回清晰的错误信息
- **缓存策略**: 使用 `CacheService` 缓存已加载数据,避免重复读取文件
- **日期格式**: 统一使用 `YYYY-MM-DD` 格式
- **平台 ID**: 使用小写 ID(zhihu, weibo, douyin 等)

### 常见问题排查

1. **配置文件不存在**: 确保 `config/config.yaml` 和 `config/frequency_words.txt` 存在
2. **MCP 服务无法启动**: 检查端口 3333 是否被占用,运行 `uv run python -m mcp_server.server`
3. **Docker 构建失败**: 检查网络连接,Dockerfile 使用重试机制下载 supercronic
4. **推送失败**: 验证 webhook URLs 和 token 是否正确,检查消息长度是否超限
5. **测试失败**: 运行 `pytest tests/ -v` 查看详细错误,检查依赖是否完整安装
6. **导入错误**: 确保从项目根目录运行,检查 PYTHONPATH 设置

### 重构迁移指南

**如果你在修改原有功能**:
1. 定位功能在 main_legacy.py 中的位置
2. 找到对应的重构模块（参考架构图）
3. 在新架构中修改对应的类和方法
4. 编写或更新单元测试
5. 运行测试确保功能正常: `pytest tests/ -v`
6. 如需要,同步更新 main_legacy.py 保持兼容

**模块对应关系**:
- 配置加载 → src/core/config.py (ConfigManager)
- 新闻爬取 → src/sources/newsnow.py (NewNowSource)
- 关键词筛选 → src/core/filter.py (NewsFilter)
- 权重计算 → src/core/ranking.py (NewsRanking)
- 报告生成 → src/core/reporter.py (NewsReporter)
- 通知推送 → src/notifiers/*.py (各通知渠道)
- 时间处理 → src/utils/time.py
- 文件操作 → src/utils/file.py
- HTTP请求 → src/utils/http.py

### 消息批次限制

不同平台有不同的消息长度限制,由 BatchSender 统一处理自动分批:
- 企业微信/Telegram: 4000 字节
- 钉钉: 20000 字节
- 飞书: 29000 字节

分批逻辑实现: src/notifiers/batch_sender.py

### 扩展平台监控

1. 访问 [newsnow](https://github.com/ourongxing/newsnow) 项目源代码
2. 在 `config/config.yaml` 的 `platforms` 中添加新平台 ID 和名称
3. 平台 ID 参考: https://github.com/ourongxing/newsnow/tree/main/server/sources

## 项目特色设计

### 关键词筛选机制

`frequency_words.txt` 支持三种语法（实现: src/core/filter.py）:
- 普通词: 标题包含任一即匹配
- 必须词(`+`): 必须同时包含才匹配
- 过滤词(`!`): 包含则排除

空行分隔词组,每组独立统计热度

### 权重算法

默认权重（实现: src/core/ranking.py）: 排名 60% + 频次 30% + 热度 10%

可通过 `config.yaml` 的 `weight` 调整:
- `rank_weight`: 看重排名高的新闻
- `frequency_weight`: 看重持续出现的新闻
- `hotness_weight`: 综合热度质量

### 插件化架构

**信息源插件**: 继承 BaseSource 即可添加新数据源（RSS、API等）
**通知器插件**: 继承 BaseNotifier 即可支持新通知渠道（Discord、Slack等）
**自动注册**: SourceRegistry 和 NotificationManager 自动发现和管理插件

### GitHub Pages 集成

- 每次运行自动生成 `index.html` 推送到仓库（src/core/reporter.py）
- 启用 GitHub Pages 后可通过网页浏览
- 支持一键保存为图片(移动端适配)

### 时区处理

- 所有时间使用**北京时间**(Asia/Shanghai)（src/utils/time.py）
- 使用 `pytz` 库处理时区转换
- GitHub Actions 运行在 UTC,通过 `TZ=Asia/Shanghai` 转换

## 重构亮点

### 代码质量提升

| 指标 | 原版本 | 重构版本 | 改进 |
|------|--------|----------|------|
| 文件数量 | 1个 | 30+个 | 模块化 |
| 最大文件行数 | 4000+ | ~400 | -90% |
| 测试覆盖 | 0% | 87个测试 | +100% |
| 可扩展性 | 低 | 高 | 插件化 |

### 设计模式应用

1. **抽象工厂模式**: BaseSource, BaseNotifier
2. **注册器模式**: SourceRegistry 自动发现信息源
3. **策略模式**: 不同的通知渠道实现
4. **模板方法模式**: BaseNotifier.send() 定义发送流程
5. **单例模式**: ConfigManager 配置管理
6. **观察者模式**: PushRecordManager 推送记录

## 相关文档

- **README.md**: 完整使用教程和部署指南（面向用户）
- **README_REFACTORED.md**: 重构版使用说明（面向开发者）
- **REFACTORING_SUMMARY.md**: 重构总结报告（架构设计和迁移指南）
- **README-Cherry-Studio.md**: Cherry Studio MCP 客户端配置教程
- **README-MCP-FAQ.md**: AI 对话分析使用指南
- **config/config.yaml**: 配置文件模板及注释
- **mcp_server/tools/**: 每个工具文件包含详细的工具说明注释
- **tests/**: 单元测试用例（最佳实践参考）

## 快速定位代码

**查找功能实现**:
- 配置管理: src/core/config.py
- 关键词筛选: src/core/filter.py (should_include_title → filter_news)
- 权重排序: src/core/ranking.py (calculate_news_weight → calculate_weights)
- 报告生成: src/core/reporter.py (generate_text_report, generate_html_report)
- 新闻爬取: src/sources/newsnow.py (fetch_news)
- 通知推送: src/notifiers/manager.py (send_notifications)
- 时间处理: src/utils/time.py (get_beijing_time, format_time_range)

**查找测试用例**:
- 配置测试: tests/test_config.py
- 核心业务测试: tests/test_core/
- 信息源测试: tests/test_sources/
- 通知器测试: tests/test_notifiers/

**示例代码**:
- RSS信息源示例: src/sources/rss.py
- 通知器实现示例: src/notifiers/feishu.py
- 测试用例示例: tests/test_models.py
