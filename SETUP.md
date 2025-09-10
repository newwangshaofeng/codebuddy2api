# CodeBuddy2API 设置指南

这个详细的设置指南将帮助你快速配置和运行 CodeBuddy2API 服务。

## 📋 前置要求

- Python 3.8 或更高版本
- 一个或多个有效的 CodeBuddy Bearer Token
- 网络连接到 CodeBuddy 官方 API (https://www.codebuddy.ai)

## 🚀 快速开始

### 1. 安装依赖

**Windows:**
```bash
start.bat
```

**手动安装:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`:
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的配置：
```bash
# 必需配置
CODEBUDDY_PASSWORD=your_secret_password_here

# 可选配置
CODEBUDDY_HOST=127.0.0.1
CODEBUDDY_PORT=8001
CODEBUDDY_API_ENDPOINT=https://www.codebuddy.ai
CODEBUDDY_CREDS_DIR=.codebuddy_creds
CODEBUDDY_LOG_LEVEL=INFO
```

### 3. 添加 CodeBuddy 认证凭证

#### 方法一：手动创建凭证文件

在 `.codebuddy_creds/` 目录下创建 JSON 格式的凭证文件：

```bash
mkdir .codebuddy_creds
```

创建文件 `.codebuddy_creds/token1.json`:
```json
{
    "bearer_token": "your_codebuddy_bearer_token_here",
    "user_id": "your_user_id_here",
    "created_at": 1725926400
}
```

#### 方法二：通过 API 添加凭证

启动服务后，使用 API 添加：
```bash
curl -X POST "http://127.0.0.1:8001/codebuddy/v1/credentials" \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "bearer_token": "your_codebuddy_token",
    "user_id": "your_user_id"
  }'
```

### 4. 获取 CodeBuddy Bearer Token

1. 登录 [CodeBuddy官网](https://www.codebuddy.ai)
2. 打开浏览器开发者工具 (F12)
3. 切换到 Network 标签页
4. 在网站上发送一个消息
5. 在网络请求中找到 API 调用
6. 查看请求的 Authorization 头，复制 Bearer token

### 5. 启动服务

```bash
python web.py
```

服务将在 `http://127.0.0.1:8001` 启动

## 🧪 测试服务

### 运行自动化测试

```bash
# 测试 API 客户端
python test_api_complete.py

# 测试 Web 服务器（需要先启动服务）
python test_api_complete.py --web-server
```

### 手动测试 API

#### 1. 健康检查
```bash
curl http://127.0.0.1:8001/health
```

#### 2. 获取模型列表
```bash
curl -X GET "http://127.0.0.1:8001/codebuddy/v1/models" \
  -H "Authorization: Bearer your_password"
```

#### 3. 发送聊天消息
```bash
curl -X POST "http://127.0.0.1:8001/codebuddy/v1/chat/completions" \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto-chat",
    "messages": [
      {"role": "user", "content": "Hello, what is 2+2?"}
    ]
  }'
```

#### 4. 流式响应
```bash
curl -X POST "http://127.0.0.1:8001/codebuddy/v1/chat/completions" \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto-chat",
    "messages": [
      {"role": "user", "content": "Write a Python hello world script"}
    ],
    "stream": true
  }'
```

## 🔧 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `CODEBUDDY_HOST` | 127.0.0.1 | 服务器地址 |
| `CODEBUDDY_PORT` | 8001 | 服务器端口 |
| `CODEBUDDY_PASSWORD` | - | API访问密码（必需） |
| `CODEBUDDY_API_ENDPOINT` | https://www.codebuddy.ai | CodeBuddy API端点 |
| `CODEBUDDY_CREDS_DIR` | .codebuddy_creds | 凭证文件目录 |
| `CODEBUDDY_LOG_LEVEL` | INFO | 日志级别 |
| `CODEBUDDY_MODELS` | auto-chat,claude-4.0,... | 可用模型列表 |

## 🐛 故障排除

### 常见问题

#### 1. "No valid CodeBuddy credentials found"
- 检查 `.codebuddy_creds` 目录是否存在且包含有效的 JSON 文件
- 验证 JSON 文件格式是否正确
- 确保 `bearer_token` 字段存在且不为空

#### 2. "API error: 401"
- 检查 Bearer Token 是否有效
- 确认 Token 没有过期
- 验证 `user_id` 是否正确

#### 3. "API error: 403"
- 检查 API 访问密码是否正确
- 确认 `CODEBUDDY_PASSWORD` 环境变量已设置

#### 4. 网络连接问题
- 检查是否能访问 `https://www.codebuddy.ai`
- 确认防火墙设置
- 检查代理配置

### 调试模式

启用详细日志：
```bash
export CODEBUDDY_LOG_LEVEL=DEBUG
python web.py
```

### 验证凭证

测试单个凭证是否有效：
```bash
curl -H "Authorization: Bearer your_token" \
     -H "X-User-Id: your_user_id" \
     https://www.codebuddy.ai/plugin/v1/models
```

## 📊 监控和日志

服务启动后会显示：
- 服务地址和端口
- 可用的 API 端点
- 认证信息
- 加载的凭证数量

日志包含：
- API 请求和响应
- 凭证轮换信息
- 错误和警告信息

## 🔐 安全注意事项

1. **保护 Bearer Token** - 不要在代码或日志中暴露
2. **设置强密码** - 使用复杂的 `CODEBUDDY_PASSWORD`
3. **网络安全** - 在生产环境中使用 HTTPS
4. **访问控制** - 限制服务的网络访问范围

## 📝 API 文档

启动服务后，访问以下端点查看完整的 API 文档：
- 服务信息: `GET /`
- 健康检查: `GET /health`
- 模型列表: `GET /codebuddy/v1/models`
- 聊天完成: `POST /codebuddy/v1/chat/completions`
- 凭证管理: `GET/POST /codebuddy/v1/credentials`

## 🤝 集成示例

查看 README.md 中的 Python 和 Node.js 客户端集成示例。