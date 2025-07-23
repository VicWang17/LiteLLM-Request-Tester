# 🤖 大模型请求测试工具 v1.0.0

一个**完全独立**的大模型请求测试工具，支持批量测试、结果分析和完整的API响应记录。

## ✨ 功能特性

- 🚀 **多次请求测试**: 可以设定调用次数，批量测试模型响应
- 📊 **结果统计**: 实时显示成功率、平均响应时间等统计信息
- 💾 **会话管理**: 自动保存测试会话，可查看历史记录
- 🎨 **美观界面**: 响应式Web界面，支持移动端访问
- ⚙️ **灵活配置**: 支持多种模型、温度、Token数等参数调整
- 🔄 **实时显示**: 测试过程实时更新，支持进度条显示
- 🧩 **双模式支持**: 
  - **简单模式**: 快速测试基本对话
  - **JSON模式**: 发送完整的API请求，支持工具调用、系统提示等高级功能
- 📝 **完整响应**: JSON模式下可查看完整的API响应对象，包括工具调用结果
- 🔧 **独立运行**: 无需依赖其他项目，开箱即用

## 🛠️ 快速开始

### 1. 安装依赖

```bash
cd request-tester
pip install -r requirements.txt
```

### 2. 配置API

编辑 `config.py` 文件，修改API配置：

```python
# API 配置（必需修改）
API_URL = "http://your-api-server:4000/v1"
API_KEY = "your-api-key"

# 支持的模型列表（可添加或删除）
AVAILABLE_MODELS = [
    "your-model-1",
    "your-model-2",
    # ... 添加更多模型
]

# 应用服务配置
HOST = "0.0.0.0"
PORT = 8001
DEBUG = True
```

### 3. 启动服务

#### 使用启动脚本（推荐）
```bash
./start.sh
```

#### 手动启动
```bash
python3 app.py
```

### 4. 访问界面

打开浏览器访问：http://localhost:8001

## 📋 配置说明

### 核心配置项

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|---------|------|
| `API_URL` | API服务地址 | `http://172.16.0.120:4000/v1` | ✅ |
| `API_KEY` | API密钥 | `sk-m4uiQWH2dD-J7bzfT4ZiBg` | ✅ |
| `AVAILABLE_MODELS` | 支持的模型列表 | 见config.py | ❌ |
| `SYSTEM_PROMPT` | 默认系统提示词 | 见config.py | ❌ |

### 应用配置项

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|---------|------|
| `HOST` | 服务监听地址 | `0.0.0.0` | ❌ |
| `PORT` | 服务端口 | `8001` | ❌ |
| `DEBUG` | 调试模式 | `True` | ❌ |
| `DEFAULT_TEMPERATURE` | 默认温度值 | `0.7` | ❌ |
| `DEFAULT_MAX_TOKENS` | 默认最大Token数 | `2000` | ❌ |
| `MAX_REQUEST_COUNT` | 最大请求次数限制 | `20` | ❌ |
| `REQUEST_TIMEOUT` | 请求超时时间（秒） | `300` | ❌ |

### 支持的模型

默认支持以下模型（可在config.py中修改）：
- `lm_studio/qwen3-coder-plus`
- `gpt-4o-mini`
- `gpt-4o`
- `qwen-max-latest`
- `claude-3-sonnet`

## 🎯 使用指南

### 简单模式
1. **选择简单模式**: 点击左上角的"简单模式"按钮
2. **输入请求内容**: 在文本框中输入要发送给大模型的内容
3. **选择模型**: 从下拉菜单中选择要测试的模型
4. **设置参数**: 
   - Temperature: 0-2（控制回答的随机性）
   - 最大Token数: 100-8000
5. **设置调用次数**: 1-20次
6. **开始测试**: 点击"开始测试"按钮

### JSON模式（高级）
1. **选择JSON模式**: 点击左上角的"JSON模式"按钮
2. **编写完整请求**: 在JSON编辑器中输入完整的API请求

#### JSON请求示例

**基础对话：**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "user",
      "content": "介绍一下人工智能的发展历程"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**工具调用：**
```json
{
  "model": "qwen-max-latest",
  "messages": [
    {
      "role": "user",
      "content": "请帮我计算 15 的平方根"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "执行数学计算",
        "parameters": {
          "type": "object",
          "required": ["expression"],
          "properties": {
            "expression": {
              "type": "string",
              "description": "要计算的数学表达式"
            }
          }
        }
      }
    }
  ],
  "temperature": 0.1
}
```

**系统提示词：**
```json
{
  "model": "claude-3-sonnet",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的代码审查专家，擅长发现代码中的问题并提供改进建议。"
    },
    {
      "role": "user",
      "content": "请审查这段Python代码：\n\ndef add(a, b):\n    return a + b"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 1500
}
```

## 📊 结果解读

每次测试结果包含：

- ✅ **成功/失败状态**: 绿色表示成功，红色表示失败
- ⏱️ **响应时间**: 每次请求的耗时
- 🔢 **Token统计**: 输入、输出和总Token数
- 📝 **响应内容**: 大模型的完整回答
- 🔧 **工具调用**: 如果有工具调用，显示调用的工具名称
- ❌ **错误信息**: 如果请求失败，显示具体错误
- 📋 **完整响应**: JSON模式下可查看原始API响应

## 🔧 API接口

工具提供以下RESTful API接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/test` | 执行模型测试 |
| `GET` | `/results/{session_id}` | 获取会话结果 |
| `GET` | `/sessions` | 获取所有会话 |
| `DELETE` | `/results/{session_id}` | 删除会话 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/config` | 获取配置信息 |
| `GET` | `/system-prompt` | 获取系统提示词 |

## 🚨 注意事项

1. **网络环境**: 确保能够访问配置的API地址
2. **API密钥**: 确保API密钥有效且有足够权限
3. **并发限制**: 建议控制调用次数，避免触发API限制
4. **数据安全**: 测试数据仅在内存中临时存储，重启后清空
5. **JSON模式**: 
   - 请确保JSON格式正确，工具会进行语法验证
   - 在JSON请求中不需要包含 `api_key` 和 `base_url`，工具会自动添加
   - 支持所有标准API参数，如 `tools`、`function_call`、`system` 等
   - 工具调用等高级功能需要模型支持

## 🔒 独立性说明

本工具已完全独立，无需依赖任何外部项目：

- ✅ **独立配置**: 使用本地 `config.py` 文件
- ✅ **独立依赖**: 仅需要 `requirements.txt` 中的包
- ✅ **独立运行**: 可在任意目录运行
- ✅ **独立部署**: 可直接部署到服务器
- ✅ **简单配置**: 直接修改 `config.py` 即可

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个工具！

## 📄 许可证

本项目采用 MIT 许可证。