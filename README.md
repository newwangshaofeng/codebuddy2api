# CodeBuddy2API

将CodeBuddy官方API包装成OpenAI兼容的API服务。直接调用CodeBuddy官方API，提供统一的接口访问。

## 功能特性

- 🔌 **OpenAI兼容接口** - 支持标准的chat completions API
- 🔄 **流式响应** - 支持实时流式输出  
- 🎯 **直接API调用** - 直接调用CodeBuddy官方API
- 🔐 **Bearer Token认证** - 使用CodeBuddy官方认证机制
- 🔄 **凭证轮换** - 支持多个认证凭证自动轮换，提高可用性
- 📊 **凭证管理** - 提供凭证添加和管理接口
- ⚡ **高性能** - 异步处理，支持并发请求
- 🎯 **透传模式** - 可选择直接转发CodeBuddy原始响应或格式转换

## 快速开始

### 1. 安装依赖

```bash
# Windows
start.bat

# 或手动安装
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

必需配置：
- `CODEBUDDY_PASSWORD` - API访问密码

### 3. 添加CodeBuddy认证凭证

在 `.codebuddy_creds` 目录下创建JSON格式的凭证文件：

```json
{
    "bearer_token": "your_codebuddy_bearer_token_here",
    "user_id": "your_user_id_here",
    "created_at": 1725926400
}
```

**如何获取CodeBuddy Bearer Token：**
1. 登录 [CodeBuddy官网](https://www.codebuddy.ai)
2. 打开浏览器开发者工具 (F12)
3. 在Network标签页中查看API请求
4. 找到Authorization头中的Bearer token
5. 复制token到凭证文件中

### 4. 启动服务

```bash
# Windows
start.bat

# 或直接运行
python web.py
```

服务将在 `http://127.0.0.1:8001` 启动

## API 使用

### 认证

所有API请求需要在Header中包含Bearer token：

```bash
Authorization: Bearer your_password_here
```

### 基本聊天

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

### 流式响应

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

### 凭证管理

查看已添加的凭证：

```bash
curl -X GET "http://127.0.0.1:8001/codebuddy/v1/credentials" \
  -H "Authorization: Bearer your_password"
```

通过API添加新凭证：

```bash
curl -X POST "http://127.0.0.1:8001/codebuddy/v1/credentials" \
  -H "Authorization: Bearer your_password" \
  -H "Content-Type: application/json" \
  -d '{
    "bearer_token": "your_codebuddy_token",
    "user_id": "your_user_id"
  }'
```

## API 端点

### 聊天完成
- `POST /codebuddy/v1/chat/completions` - 发送消息给CodeBuddy
- `GET /codebuddy/v1/models` - 获取可用模型列表

### 凭证管理
- `GET /codebuddy/v1/credentials` - 列出所有凭证
- `POST /codebuddy/v1/credentials` - 添加新凭证

### 系统
- `GET /health` - 健康检查
- `GET /` - 服务信息

## 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `CODEBUDDY_HOST` | 127.0.0.1 | 服务器地址 |
| `CODEBUDDY_PORT` | 8001 | 服务器端口 |
| `CODEBUDDY_PASSWORD` | - | API访问密码（必需） |
| `CODEBUDDY_API_ENDPOINT` | https://www.codebuddy.ai | CodeBuddy API端点 |
| `CODEBUDDY_CREDS_DIR` | .codebuddy_creds | 凭证文件目录 |
| `CODEBUDDY_LOG_LEVEL` | INFO | 日志级别 |
| `CODEBUDDY_MODELS` | auto-chat,claude-4.0,gpt-5... | 可用模型列表 |
| `CODEBUDDY_PASSTHROUGH` | true | 透传模式：true=直接转发，false=格式转换 |

## 集成示例

### Python客户端

```python
import openai

client = openai.OpenAI(
    api_key="your_password",
    base_url="http://127.0.0.1:8001/codebuddy/v1"
)

response = client.chat.completions.create(
    model="auto-chat",
    messages=[
        {"role": "user", "content": "Help me debug this Python code"}
    ]
)

print(response.choices[0].message.content)
```

### Node.js客户端

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
    apiKey: 'your_password',
    baseURL: 'http://127.0.0.1:8001/codebuddy/v1'
});

async function chat() {
    const response = await client.chat.completions.create({
        model: 'auto-chat',
        messages: [
            { role: 'user', content: 'Create a new React component' }
        ]
    });
    
    console.log(response.choices[0].message.content);
}
```

## 透传模式

### 什么是透传模式？

透传模式控制API响应的处理方式：

- **透传模式 (true)** - 直接转发CodeBuddy的原始响应，无格式转换
- **转换模式 (false)** - 将响应转换为标准OpenAI格式

### 推荐设置

**推荐使用透传模式**（默认启用），因为：
- CodeBuddy返回的已经是标准OpenAI格式
- 性能更好，避免不必要的转换开销
- 保持响应完整性，避免信息丢失

```bash
# 启用透传模式（推荐）
CODEBUDDY_PASSTHROUGH=true

# 禁用透传模式
CODEBUDDY_PASSTHROUGH=false
```

## 注意事项

1. **认证凭证** - 需要有效的CodeBuddy Bearer Token
2. **API限制** - 遵循CodeBuddy官方API的使用限制和速率限制
3. **凭证轮换** - 支持多个凭证自动轮换，提高服务可用性
4. **网络连接** - 需要能够访问 https://www.codebuddy.ai
5. **模型支持** - 支持CodeBuddy官方提供的所有模型
6. **透传模式** - 默认启用，大多数情况下无需修改

## 故障排除

### 认证失败
```bash
# 检查凭证文件格式
cat .codebuddy_creds/your_credential.json

# 确保bearer_token有效
curl -H "Authorization: Bearer your_token" https://www.codebuddy.ai/plugin/v1/models
```

### API调用失败
1. 检查网络连接
2. 验证API端点是否正确
3. 确认token未过期

### 凭证管理
- 凭证文件必须是有效的JSON格式
- bearer_token字段是必需的
- 支持添加多个凭证文件进行轮换