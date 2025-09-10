# CodeBuddy2API 项目结构

## 📁 文件结构

```
codebuddy2api/
├── src/                           # 源代码目录
│   ├── auth.py                    # 认证模块
│   ├── models.py                  # 数据模型定义
│   ├── codebuddy_api_client.py    # CodeBuddy API 客户端
│   ├── codebuddy_token_manager.py # 凭证管理器
│   └── codebuddy_router.py        # API 路由处理
├── .codebuddy_creds/              # 凭证文件目录
├── web.py                         # 主服务入口
├── config.py                      # 配置管理
├── requirements.txt               # 依赖列表
├── .env.example                   # 环境变量模板
├── start.bat                      # Windows 启动脚本
├── test_api_complete.py           # 完整测试脚本
├── README.md                      # 项目文档
├── SETUP.md                       # 详细设置指南
└── PROJECT_STRUCTURE.md           # 项目结构说明
```

## 🔧 核心模块说明

### web.py
- 主服务入口文件
- 配置 FastAPI 应用
- 设置 CORS 中间件
- 挂载 API 路由

### src/codebuddy_router.py
- 处理所有 API 路由
- `/v1/models` - 获取可用模型
- `/v1/chat/completions` - 聊天完成
- `/v1/credentials` - 凭证管理

### src/codebuddy_api_client.py
- CodeBuddy 官方 API 客户端
- 处理 HTTP 请求和响应
- 支持流式和非流式调用
- 错误处理和重试机制

### src/codebuddy_token_manager.py
- 管理多个认证凭证
- 自动轮换凭证使用
- 凭证文件加载和验证

### src/models.py
- Pydantic 数据模型定义
- OpenAI 兼容的请求/响应格式
- 类型验证和序列化

### src/auth.py
- API 认证中间件
- Bearer Token 验证
- 访问控制

### config.py
- 环境变量配置管理
- 默认值设置
- 配置项获取函数

## 🌐 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/` | GET | 服务信息 |
| `/codebuddy/v1/models` | GET | 获取模型列表 |
| `/codebuddy/v1/chat/completions` | POST | 聊天完成 |
| `/codebuddy/v1/credentials` | GET/POST | 凭证管理 |

## 🔄 数据流向

```
客户端请求 
    ↓
认证中间件验证 
    ↓
API路由处理 
    ↓
凭证管理器获取Token 
    ↓
API客户端调用CodeBuddy 
    ↓
响应处理和格式化 
    ↓
返回给客户端
```

## 🛡️ 安全设计

1. **Bearer Token 认证** - 所有 API 调用需要认证
2. **凭证隔离** - 凭证文件独立存储
3. **错误处理** - 不暴露敏感信息
4. **CORS 配置** - 跨域访问控制

## ⚡ 性能特性

1. **异步处理** - 基于 AsyncIO 的高性能架构
2. **凭证轮换** - 多凭证负载均衡
3. **流式响应** - 实时数据传输
4. **连接复用** - HTTP 连接池优化

## 🔧 配置项

所有配置通过环境变量管理，支持 `.env` 文件加载：

- `CODEBUDDY_HOST` - 服务器地址
- `CODEBUDDY_PORT` - 服务器端口  
- `CODEBUDDY_PASSWORD` - API 访问密码
- `CODEBUDDY_API_ENDPOINT` - CodeBuddy API 端点
- `CODEBUDDY_CREDS_DIR` - 凭证文件目录
- `CODEBUDDY_LOG_LEVEL` - 日志级别
- `CODEBUDDY_MODELS` - 支持的模型列表