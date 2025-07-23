# 🚀 部署指南

## 📋 部署前检查清单

在将项目部署到生产环境或分享给其他人之前，请确保：

### ✅ 安全检查
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 没有在代码中硬编码API密钥
- [ ] `.env.example` 文件已更新为最新的配置模板
- [ ] 敏感信息已从版本控制中移除

### ✅ 配置检查
- [ ] 环境变量配置正确
- [ ] API连接测试通过
- [ ] 所有依赖已安装
- [ ] 应用可以正常启动

## 🔧 本地开发设置

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd LiteLLM-Request-Tester
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的配置
nano .env
```

### 4. 测试配置
```bash
# 测试环境变量配置
python test_env_config.py

# 启动应用
python app.py
```

## 🌐 生产环境部署

### Docker 部署（推荐）

1. **创建 Dockerfile**：
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8005

CMD ["python", "app.py"]
```

2. **构建和运行**：
```bash
# 构建镜像
docker build -t llm-request-tester .

# 运行容器（使用环境变量）
docker run -d \
  --name llm-tester \
  -p 8005:8005 \
  -e API_URL="your-api-url" \
  -e API_KEY="your-api-key" \
  llm-request-tester
```

### 传统部署

1. **服务器准备**：
```bash
# 安装Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-pip

# 克隆项目
git clone <your-repo-url>
cd LiteLLM-Request-Tester
```

2. **配置环境**：
```bash
# 安装依赖
pip3 install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env
```

3. **使用 systemd 管理服务**：
```bash
# 创建服务文件
sudo nano /etc/systemd/system/llm-tester.service
```

服务文件内容：
```ini
[Unit]
Description=LLM Request Tester
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/LiteLLM-Request-Tester
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable llm-tester
sudo systemctl start llm-tester
```

## 🔒 安全最佳实践

### 环境变量管理
- 使用 `.env` 文件管理本地开发配置
- 生产环境使用系统环境变量或密钥管理服务
- 定期轮换API密钥

### 网络安全
- 使用HTTPS（建议配置反向代理）
- 限制访问IP（如果需要）
- 配置防火墙规则

### 监控和日志
- 监控应用性能和错误
- 配置日志轮转
- 设置告警机制

## 🤝 团队协作

### 新成员加入流程
1. 克隆项目仓库
2. 复制 `.env.example` 为 `.env`
3. 联系管理员获取API配置信息
4. 运行 `python test_env_config.py` 验证配置
5. 启动应用开始开发

### 配置更新流程
1. 更新 `.env.example` 文件（如果有新的配置项）
2. 通知团队成员更新本地 `.env` 文件
3. 更新部署文档和README

## 🆘 故障排除

### 常见问题

**问题：应用启动失败，提示环境变量未设置**
```
解决方案：
1. 检查 .env 文件是否存在
2. 确认 .env 文件中的变量名称正确
3. 运行 python test_env_config.py 验证配置
```

**问题：API调用失败**
```
解决方案：
1. 检查API_URL是否正确
2. 验证API_KEY是否有效
3. 确认网络连接正常
4. 查看服务器日志获取详细错误信息
```

**问题：端口被占用**
```
解决方案：
1. 修改 .env 文件中的 PORT 配置
2. 或者停止占用端口的其他服务
```