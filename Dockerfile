# 使用官方的、轻量级的 Python 镜像作为基础
FROM python:3.11-slim

# 设置容器内的工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
# --no-cache-dir 选项可以减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 将项目的所有文件复制到工作目录中
COPY . .

# 安装 gosu，一个轻量级的 su/sudo 替代品，用于在脚本中切换用户
# 并在同一层中进行清理以减小镜像体积
RUN apt-get update && \
    apt-get install -y gosu && \
    rm -rf /var/lib/apt/lists/*

# 创建一个非root用户来运行应用
RUN useradd -m -u 1001 appuser

# 设置目录权限并直接运行服务
RUN chown -R appuser:appuser /app && \
    chown -R appuser:appuser /usr/local/bin

# 声明容器将要监听的端口
# 这个端口应该与您在配置中设置的 CODEBUDDY_PORT 一致
EXPOSE 8001

# 定义容器启动时要执行的命令
# 使用 Hypercorn 启动，它是一个生产级的 ASGI 服务器
CMD ["gosu", "appuser", "hypercorn", "web:app", "--bind", "0.0.0.0:8001"]