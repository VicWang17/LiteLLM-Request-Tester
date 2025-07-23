#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务启动脚本
"""

import uvicorn
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 测试导入
    from config import DEFAULT_MODEL, HOST, PORT
    print(f"配置加载成功:")
    print(f"  默认模型: {DEFAULT_MODEL}")
    print(f"  主机: {HOST}")
    print(f"  端口: {PORT}")
    
    # 测试应用导入
    from app import app
    print("应用导入成功")
    
    # 启动服务
    print(f"启动服务在 http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, reload=False)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()