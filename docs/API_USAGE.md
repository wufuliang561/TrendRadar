# TrendRadar API 使用指南

TrendRadar API 提供基于大模型的热点新闻智能分析功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置大模型 API

在 `config/config.yaml` 中配置大模型参数,或通过环境变量设置（推荐）:

```bash
# OpenAI
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4"

# DeepSeek
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"

# Moonshot
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.moonshot.cn/v1"
export LLM_MODEL="moonshot-v1-8k"

# 本地 Ollama
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_MODEL="llama3"
export LLM_API_KEY="not-required"  # 本地模型不需要 API Key
```

### 3. 启动服务器

```bash
# 方式一: 使用启动脚本（推荐）
./start-api.sh

# 方式二: 直接使用 uvicorn
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 方式三: 运行 Python 模块
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

服务器启动后访问:
- **API 文档**: http://localhost:8000/docs (Swagger UI)
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

---

## 📡 API 接口说明

### 系统相关

#### 1. 获取系统状态

```bash
GET /api/v1/system/status
```

返回服务器运行状态、活跃会话数等信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "service": "TrendRadar API",
    "version": "1.0.0",
    "status": "running",
    "uptime": "2小时30分钟",
    "llm_configured": true,
    "storage_path": "conversations",
    "active_sessions": 5
  }
}
```

#### 2. 获取配置信息

```bash
GET /api/v1/system/config
```

返回当前的系统配置（不包含敏感信息）。

#### 3. 获取最新新闻

```bash
GET /api/v1/news/latest?platforms=zhihu,weibo&limit=50
```

**参数**:
- `platforms`: 平台筛选,多个用逗号分隔（可选）
- `limit`: 返回数量限制（默认 50）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 50,
    "date": "2025年11月12日",
    "news": [
      {
        "title": "新闻标题",
        "platform": "知乎",
        "rank": 1,
        "count": 3,
        "weight": 85.6
      }
    ]
  }
}
```

### 对话相关

#### 4. 创建会话

```bash
POST /api/v1/chat/sessions
Content-Type: application/json

{
  "inject_context": true,
  "platforms": ["zhihu", "weibo"],
  "news_limit": 50
}
```

**参数说明**:
- `inject_context`: 是否自动注入最新新闻数据（首轮建议 true）
- `platforms`: 平台筛选（可选）
- `news_limit`: 注入的新闻数量（默认 50）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "session_id": "uuid-xxx",
    "created_at": "2025-11-12T16:32:00",
    "context_injected": true,
    "news_count": 50
  },
  "message": "会话创建成功"
}
```

#### 5. 发送消息

```bash
POST /api/v1/chat/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "分析今天知乎和微博的热点,有什么共同话题?",
  "inject_context": false
}
```

**参数说明**:
- `message`: 用户消息（必填）
- `inject_context`: 是否重新注入最新数据（可选,用于更新上下文）
- `platforms`: 平台筛选（可选）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "reply": "根据数据分析,今天知乎和微博的共同热点有...",
    "session_id": "uuid-xxx",
    "timestamp": "2025-11-12T16:35:00",
    "token_usage": {
      "prompt_tokens": 1500,
      "completion_tokens": 300,
      "total_tokens": 1800
    }
  },
  "message": "消息发送成功"
}
```

#### 6. 获取会话历史

```bash
GET /api/v1/chat/sessions/{session_id}
```

返回完整的会话信息和消息历史。

#### 7. 删除会话

```bash
DELETE /api/v1/chat/sessions/{session_id}
```

永久删除指定会话。

#### 8. 列出所有会话

```bash
GET /api/v1/chat/sessions?limit=100
```

返回所有会话 ID 列表（按修改时间倒序）。

---

## 💡 使用示例

### Python 客户端示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. 创建会话
resp = requests.post(f"{BASE_URL}/chat/sessions", json={
    "inject_context": True,
    "platforms": ["zhihu", "weibo"],
    "news_limit": 50
})
session_id = resp.json()["data"]["session_id"]
print(f"会话创建成功: {session_id}")

# 2. 发送消息
resp = requests.post(
    f"{BASE_URL}/chat/sessions/{session_id}/messages",
    json={
        "message": "总结今天最热门的 5 条新闻,并分析趋势"
    }
)
reply = resp.json()["data"]["reply"]
print(f"AI 回复: {reply}")

# 3. 继续对话
resp = requests.post(
    f"{BASE_URL}/chat/sessions/{session_id}/messages",
    json={
        "message": "这些新闻中有哪些是科技相关的?"
    }
)
print(f"AI 回复: {resp.json()['data']['reply']}")

# 4. 获取会话历史
resp = requests.get(f"{BASE_URL}/chat/sessions/{session_id}")
messages = resp.json()["data"]["messages"]
print(f"共 {len(messages)} 条消息")
```

### JavaScript/前端示例

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

async function startChat() {
    // 1. 创建会话
    const session = await fetch(`${BASE_URL}/chat/sessions`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            inject_context: true,
            platforms: ['zhihu'],
            news_limit: 30
        })
    }).then(r => r.json());

    const sessionId = session.data.session_id;
    console.log('会话创建成功:', sessionId);

    // 2. 发送消息
    const response = await fetch(
        `${BASE_URL}/chat/sessions/${sessionId}/messages`,
        {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: '分析今天知乎的热点话题'
            })
        }
    ).then(r => r.json());

    console.log('AI 回复:', response.data.reply);
    console.log('Token 使用:', response.data.token_usage);
}

startChat();
```

### curl 示例

```bash
# 1. 创建会话
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"inject_context": true}' \
  | jq -r '.data.session_id')

echo "会话 ID: $SESSION_ID"

# 2. 发送消息
curl -X POST http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "总结今天的热点新闻"}' \
  | jq '.data.reply'

# 3. 获取会话历史
curl http://localhost:8000/api/v1/chat/sessions/$SESSION_ID | jq
```

---

## ⚙️ 配置说明

### 大模型配置 (config.yaml)

```yaml
llm:
  provider: "openai"  # 服务商标识
  base_url: "https://api.openai.com/v1"  # API 基础 URL
  api_key: ""  # 建议通过环境变量配置
  model: "gpt-4"  # 模型名称
  max_tokens: 2000  # 最大生成 Token 数
  temperature: 0.7  # 温度参数（0-2）
  timeout: 60  # 超时时间（秒）
```

### 对话配置 (config.yaml)

```yaml
chat:
  storage_path: "conversations"  # 会话存储目录
  max_history_length: 20  # 单个会话保留的最大历史消息数
  context_news_limit: 50  # 首轮对话注入的最大新闻数量
  enable_streaming: false  # 流式输出（未来功能）
```

### 环境变量优先级

环境变量会覆盖配置文件中的设置:

```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.example.com/v1"
export LLM_MODEL="gpt-4"
export LLM_MAX_TOKENS="2000"
export LLM_TEMPERATURE="0.7"
export LLM_TIMEOUT="60"
```

---

## 🔧 常见问题

### 1. API Key 未配置

**错误**: `警告: 未配置 API Key`

**解决方法**:
```bash
export LLM_API_KEY="your-api-key"
./start-api.sh
```

### 2. 端口被占用

**错误**: `Address already in use`

**解决方法**:
```bash
# 查找占用 8000 端口的进程
lsof -i:8000

# 杀死进程或更换端口
uvicorn src.api.server:app --port 8001
```

### 3. 未找到新闻数据

**错误**: `未找到 2025年11月12日 的新闻数据`

**原因**: 今天还没有运行爬虫或数据文件不存在。

**解决方法**:
```bash
# 先运行爬虫生成数据
python main.py

# 然后启动 API 服务器
./start-api.sh
```

### 4. Token 使用量过大

**问题**: 每次请求消耗大量 Token

**优化建议**:
- 减少 `news_limit` 参数（默认 50 → 20-30）
- 减少 `max_history_length`（默认 20 → 10）
- 首轮对话后将 `inject_context` 设为 `false`

---

## 📊 数据格式说明

### 精简的新闻数据格式

为了节省 Token,首轮对话注入的新闻数据仅包含核心字段:

```json
{
  "title": "新闻标题",
  "platform": "知乎",
  "rank": 1,
  "count": 3,
  "weight": 85.6
}
```

**字段说明**:
- `title`: 新闻标题
- `platform`: 来源平台
- `rank`: 在平台的排名（越小越热门）
- `count`: 在不同批次中出现的次数（持续热度）
- `weight`: 综合权重分数（0-100,越高越重要）

**优化效果**: 相比完整数据节省约 60% Token

---

## 🚢 生产部署

### Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行:

```bash
docker build -t trendradar-api .

docker run -d \
  --name trendradar-api \
  -p 8000:8000 \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="https://api.openai.com/v1" \
  -e LLM_MODEL="gpt-4" \
  -v $(pwd)/conversations:/app/conversations \
  -v $(pwd)/output:/app/output:ro \
  trendradar-api
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 📚 相关文档

- **API 在线文档**: http://localhost:8000/docs
- **项目主文档**: [README.md](../README.md)
- **架构设计**: [REFACTORING_SUMMARY.md](../REFACTORING_SUMMARY.md)
- **MCP 服务器**: [README-MCP-FAQ.md](../README-MCP-FAQ.md)

---

## 💬 技术支持

如有问题,请提交 Issue: https://github.com/sansan0/TrendRadar/issues
