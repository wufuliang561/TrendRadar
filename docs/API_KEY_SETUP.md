# 🔑 API 密钥配置指南

## 快速开始（DeepSeek）

### 方式一：使用配置脚本（推荐）

1. **复制示例文件**
```bash
cp setup-deepseek-demo.sh setup-deepseek.sh
```

2. **编辑配置文件，填入你的 API Key**
```bash
# 使用你喜欢的编辑器打开
vim setup-deepseek.sh
# 或
nano setup-deepseek.sh

# 将这一行:
export LLM_API_KEY="sk-your-deepseek-api-key-here"
# 改为你的真实 API Key:
export LLM_API_KEY="sk-abc123xyz..."
```

3. **加载配置**
```bash
source setup-deepseek.sh
```

4. **启动服务器**
```bash
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

---

### 方式二：使用 .env 文件

1. **创建 .env 文件**
```bash
cp .env.example .env
```

2. **编辑 .env，填入你的 API Key**
```bash
vim .env

# 内容示例:
LLM_API_KEY=sk-your-deepseek-api-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

3. **加载并启动**
```bash
# 加载环境变量
export $(cat .env | xargs)

# 启动服务
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

---

### 方式三：直接设置环境变量

```bash
# 临时设置（当前终端会话有效）
export LLM_API_KEY="sk-your-deepseek-api-key-here"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"

# 启动服务
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

---

## 🔑 获取 DeepSeek API Key

1. 访问: https://platform.deepseek.com
2. 注册/登录账号
3. 进入 API Keys 页面: https://platform.deepseek.com/api_keys
4. 点击「创建 API Key」
5. 复制生成的 Key（格式: `sk-...`）

---

## 💰 DeepSeek 定价（非常便宜）

| 项目 | 价格 | 说明 |
|------|------|------|
| 输入 | ¥0.001 / 1K tokens | 约 750 个汉字 |
| 输出 | ¥0.002 / 1K tokens | 约 750 个汉字 |
| 新用户 | 赠送 500 万 tokens | 足够测试和开发 |

**示例成本**:
- 一次完整对话（2500 tokens）: ≈ ¥0.005（5 厘）
- 1000 次对话: ≈ ¥5

---

## 🎯 其他大模型配置

### OpenAI（GPT-4）

```bash
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4"
```

获取地址: https://platform.openai.com/api-keys

### Moonshot（月之暗面）

```bash
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.moonshot.cn/v1"
export LLM_MODEL="moonshot-v1-8k"
```

获取地址: https://platform.moonshot.cn

### 本地 Ollama（免费）

```bash
# 1. 安装 Ollama: https://ollama.com
brew install ollama  # macOS

# 2. 下载模型
ollama pull llama3

# 3. 启动服务
ollama serve

# 4. 配置环境变量
export LLM_API_KEY="not-required"
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_MODEL="llama3"
```

---

## ✅ 验证配置

启动服务后，访问系统状态接口:

```bash
curl http://localhost:8000/api/v1/system/status | python3 -m json.tool
```

查看 `llm_configured` 字段:
- `true`: 配置成功 ✓
- `false`: 需要检查 API Key

---

## 🔒 安全提示

1. **不要提交 API Key 到 Git**
   - `.env` 和 `setup-deepseek.sh` 已添加到 `.gitignore`
   - 仅提交示例文件 `.env.example` 和 `setup-deepseek-demo.sh`

2. **定期轮换 API Key**
   - 建议每 3-6 个月更换一次

3. **限制 API Key 权限**
   - 仅授予必要的权限
   - 设置使用限额

---

## 🛠️ 故障排查

### 1. 提示 "未配置 LLM API Key"

**原因**: 环境变量未设置或未生效

**解决**:
```bash
# 检查环境变量
echo $LLM_API_KEY

# 如果为空，重新加载配置
source setup-deepseek.sh
```

### 2. API 调用失败

**检查步骤**:
```bash
# 1. 测试 API 连通性
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"

# 2. 检查余额
# 访问: https://platform.deepseek.com/usage

# 3. 查看服务器日志
# 日志会显示详细的错误信息
```

### 3. Token 不足

**解决**:
- 充值: https://platform.deepseek.com/usage
- 新用户有 500 万 tokens 免费额度

---

## 📞 技术支持

- **DeepSeek 官方文档**: https://platform.deepseek.com/docs
- **项目文档**: `docs/API_USAGE.md`
- **在线 API 文档**: http://localhost:8000/docs

---

## 🚀 一键启动（推荐流程）

```bash
# 1. 配置 DeepSeek API Key
cp setup-deepseek-demo.sh setup-deepseek.sh
vim setup-deepseek.sh  # 填入真实 API Key
source setup-deepseek.sh

# 2. 生成新闻数据（可选）
python main.py

# 3. 启动 API 服务器
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# 4. 测试流式对话
python3 example_stream_chat.py

# 5. 访问 API 文档
open http://localhost:8000/docs
```

配置完成后，享受使用! 🎉
