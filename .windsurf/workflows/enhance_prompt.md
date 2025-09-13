---
description: 提示词增强工作流，结合项目上下文和文件变更生成更准确的提示词
---

# AI 实现方案生成工作流

此工作流通过分析项目结构和上下文，将用户需求转化为结构化的实现方案，为AI开发者提供清晰的开发指导。

## 使用说明

1. 描述您想要实现的功能或解决的问题
2. 指定相关的代码文件（可选）
3. 系统将生成包含详细实现方案的提示词

## 工作流步骤

### 1. 分析项目结构

```python
def analyze_project_structure():
    """
    分析项目结构，识别关键组件和模块
    返回：
        - 项目类型（如：FastAPI Web服务）
        - 主要模块和功能
        - 技术栈信息
        - 配置方式
    """
    return {
        "project_type": "FastAPI Web服务",
        "tech_stack": ["Python 3.8+", "FastAPI", "Pydantic", "JWT认证", "RESTful API"],
        "main_components": [
            "认证模块 (auth.py)",
            "API客户端 (codebuddy_api_client.py)",
            "认证路由 (codebuddy_auth_router.py)",
            "主API路由 (codebuddy_router.py)",
            "令牌管理 (codebuddy_token_manager.py)",
            "前端路由 (frontend_router.py)",
            "数据模型 (models.py)",
            "设置路由 (settings_router.py)",
            "使用统计 (usage_stats_manager.py)"
        ],
        "config_approach": "环境变量 + 配置文件 (config.py)",
        "dependency_management": "requirements.txt"
    }
```

### 2. 需求分析框架

```python
def analyze_requirements(user_prompt, file_context=None):
    """
    分析用户需求，提取关键要素
    
    参数:
        user_prompt (str): 用户原始需求
        file_context (dict): 相关文件内容（如果有）
        
    返回:
        dict: 结构化的需求分析结果
    """
    return {
        "core_functionality": "描述核心功能需求",
        "api_endpoints": ["列出需要添加/修改的API端点"],
        "data_models": ["涉及的数据模型"],
        "dependencies": ["需要的新依赖项"],
        "security_considerations": ["安全考虑"],
        "error_handling": ["错误处理需求"],
        "testing_requirements": ["测试需求"]
    }
```

### 3. 生成实现方案

```python
generate_implementation_plan(user_prompt, file_paths=None):
    """
    生成结构化的实现方案
    
    参数:
        user_prompt (str): 用户原始需求
        file_paths (list): 相关文件路径列表（可选）
        
    返回:
        str: 结构化的实现方案
    """
    # 1. 分析项目结构
    project_info = analyze_project_structure()
    
    # 2. 分析需求
    requirements = analyze_requirements(user_prompt)
    
    # 3. 构建实现方案
    plan = f"""
# 实现方案: {requirements['core_functionality']}

## 1. 项目背景
- 项目类型: {project_info['project_type']}
- 技术栈: {', '.join(project_info['tech_stack'])}
- 主要模块: {', '.join(project_info['main_components'])}

## 2. 需求分析
{user_prompt}

## 3. 实现步骤
1. **API设计**
   - 端点: {', '.join(requirements['api_endpoints']) if requirements['api_endpoints'] else '待确定'}
   - 请求/响应模型: {', '.join(requirements['data_models']) if requirements['data_models'] else '待确定'}

2. **代码实现**
   - 需要修改的文件: {', '.join(file_paths) if file_paths else '待确定'}
   - 新文件: 待确定
   - 依赖项: {', '.join(requirements['dependencies']) if requirements['dependencies'] else '无'}

3. **测试计划**
   - 单元测试: 待补充
   - 集成测试: 待补充
   - 性能测试: 待补充

4. **部署考虑**
   - 配置变更: 待确定
   - 数据库迁移: 如适用
   - 监控指标: 待确定

## 4. 安全考虑
{'- ' + '\n- '.join(requirements['security_considerations']) if requirements['security_considerations'] else '无特殊安全考虑'}

## 5. 错误处理
{'- ' + '\n- '.join(requirements['error_handling']) if requirements['error_handling'] else '标准错误处理流程'}

## 6. 后续优化方向
1. 性能优化
2. 代码重构
3. 功能扩展
"""
    return plan
```

### 4. 使用示例

```python
# 示例：生成状态监控端点的实现方案
user_requirement = """
我需要添加一个状态监控端点，用于：
1. 实时监控服务健康状态
2. 收集性能指标（CPU、内存、请求数）
3. 提供基本的诊断信息
"""

# 指定相关文件
related_files = [
    "src/codebuddy_router.py",
    "web.py",
    "src/settings_router.py"
]

# 生成实现方案
implementation_plan = generate_implementation_plan(user_requirement, related_files)
print(implementation_plan)
```

## 使用场景

1. **功能开发**：将业务需求转化为技术实现方案
2. **系统设计**：设计新的系统组件或服务
3. **技术调研**：评估不同实现方案的优缺点
4. **代码重构**：规划代码重构路线图

## 最佳实践

1. **明确需求**：
   - 清晰描述功能目标和业务价值
   - 指定性能、安全等方面的特殊要求
   - 提供相关业务场景和用例

2. **上下文信息**：
   - 提供相关模块的文件路径
   - 说明与现有功能的集成点
   - 列出已知的技术约束或依赖

3. **迭代优化**：
   - 先关注整体架构，再深入细节
   - 分阶段实现复杂功能
   - 明确每个迭代的交付目标

4. **质量保证**：
   - 定义验收标准
   - 规划测试策略
   - 考虑监控和可观测性需求

## 输出格式

实现方案将包含以下部分：
1. **项目背景**：技术栈和架构概览
2. **需求分析**：功能需求和非功能需求
3. **实现步骤**：详细的开发任务分解
4. **测试计划**：测试策略和用例
5. **部署指南**：部署步骤和配置变更
6. **后续优化**：未来改进方向
