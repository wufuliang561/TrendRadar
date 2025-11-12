# 🚀 快速启动指南

## 方式一: 一键启动（推荐）

适合第一次使用或完整部署的场景。

```bash
./start-all.sh
```

**功能**:
- ✅ 自动检查 Python 环境
- ✅ 自动安装/更新依赖
- ✅ 交互式配置 API Key
- ✅ 生成新闻数据
- ✅ 启动 API 服务器
- ✅ 显示完整的使用说明

**适用场景**:
- 第一次使用
- 需要配置 API Key
- 需要重新安装依赖
- 需要重新生成新闻数据

---

## 方式二: 快速启动

适合已配置好环境,只需快速启动的场景。

```bash
./quick-start.sh
```

**前提条件**:
- 已安装依赖
- 已配置 API Key（通过 `source setup-deepseek.sh`）

**功能**:
- ✅ 检查依赖（如缺失会自动安装）
- ✅ 验证 API Key
- ✅ 生成新闻数据（如果今天还没有）
- ✅ 启动 API 服务器

---

## 方式三: 手动启动

完全手动控制每一步。

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 配置 API Key

**选项 A: 使用配置脚本**
```bash
# 复制并编辑配置文件
cp setup-deepseek-demo.sh setup-deepseek.sh
vim setup-deepseek.sh  # 填入你的真实 API Key

# 加载配置
source setup-deepseek.sh
```

**选项 B: 直接设置环境变量**
```bash
export LLM_API_KEY="sk-your-api-key-here"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
```

### 3. 生成新闻数据

```bash
python3 main.py
```

### 4. 启动 API 服务器

```bash
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

---

## 📋 启动脚本对比

| 特性 | start-all.sh | quick-start.sh | 手动启动 |
|------|--------------|----------------|----------|
| 环境检查 | ✅ 完整检查 | ✅ 基础检查 | ❌ 需手动 |
| 依赖安装 | ✅ 自动 | ✅ 按需 | ❌ 需手动 |
| API Key 配置 | ✅ 交互式 | ⚠️  需预先配置 | ❌ 需手动 |
| 新闻生成 | ✅ 自动/选择 | ✅ 按需 | ❌ 需手动 |
| 端口冲突处理 | ✅ 自动 | ✅ 自动 | ❌ 需手动 |
| 使用难度 | 🟢 简单 | 🟡 中等 | 🔴 复杂 |

---

## 🔑 获取 DeepSeek API Key

1. 访问: https://platform.deepseek.com
2. 注册/登录账号
3. 进入 API Keys 页面: https://platform.deepseek.com/api_keys
4. 创建 API Key
5. 复制 Key（格式: `sk-...`）

详细配置指南: [docs/API_KEY_SETUP.md](docs/API_KEY_SETUP.md)

---

## ✅ 验证启动成功

启动后,访问以下地址验证:

```bash
# 健康检查
curl http://localhost:8000/health

# 系统状态
curl http://localhost:8000/api/v1/system/status | python3 -m json.tool

# API 文档
open http://localhost:8000/docs
```

---

## 🧪 测试功能

### 运行测试脚本

```bash
# 基础功能测试
python3 test_api.py

# 普通对话示例
python3 example_api_usage.py

# 流式输出示例（推荐）⭐
python3 example_stream_chat.py
```

---

## 🛑 停止服务

```bash
# 方式一: 在运行窗口按 Ctrl+C

# 方式二: 查找并杀死进程
lsof -ti:8000 | xargs kill -9

# 方式三: 使用脚本显示的 PID
kill <PID>
```

---

## 📚 相关文档

- **完整使用指南**: [docs/API_USAGE.md](docs/API_USAGE.md)
- **API Key 配置**: [docs/API_KEY_SETUP.md](docs/API_KEY_SETUP.md)
- **实现总结**: [docs/AI_CHAT_IMPLEMENTATION.md](docs/AI_CHAT_IMPLEMENTATION.md)
- **在线 API 文档**: http://localhost:8000/docs

---

## 🐛 常见问题

### 1. 提示 "命令未找到: python3"

**解决**:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt-get install python3
```

### 2. 提示 "端口 8000 已被占用"

**解决**:
```bash
# 查看占用进程
lsof -i:8000

# 杀死进程
kill -9 <PID>

# 或使用 start-all.sh，会自动处理
./start-all.sh
```

### 3. 提示 "未配置 LLM API Key"

**解决**:
```bash
# 配置 DeepSeek API Key
cp setup-deepseek-demo.sh setup-deepseek.sh
vim setup-deepseek.sh  # 填入真实 API Key
source setup-deepseek.sh
```

### 4. 依赖安装失败

**解决**:
```bash
# 升级 pip
pip3 install --upgrade pip

# 重新安装
pip3 install -r requirements.txt

# 如果还是失败，尝试清理缓存
pip3 cache purge
pip3 install --no-cache-dir -r requirements.txt
```

---

## 🎉 推荐使用流程

**首次使用**:
```bash
# 1. 一键启动（会引导配置）
./start-all.sh
```

**日常使用**:
```bash
# 1. 加载 API Key
source setup-deepseek.sh

# 2. 快速启动
./quick-start.sh

# 3. 测试流式对话
python3 example_stream_chat.py
```

---

需要帮助? 查看完整文档或提交 Issue! 🚀
