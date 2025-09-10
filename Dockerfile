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

# 声明容器将要监听的端口
# 这个端口应该与您在配置中设置的 CODEBUDDY_PORT 一致
EXPOSE 8001

# 定义容器启动时要执行的命令
CMD ["python", "web.py"]