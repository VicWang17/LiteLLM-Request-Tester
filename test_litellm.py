#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试litellm调用
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_litellm():
    try:
        import litellm
        print(f"✓ LiteLLM导入成功，版本: {litellm.__version__}")
        
        # 从配置文件读取参数
        from config import API_URL, API_KEY, DEFAULT_MODEL
        print(f"✓ 配置加载成功:")
        print(f"  API_URL: {API_URL}")
        print(f"  API_KEY: {API_KEY[:10]}...")
        print(f"  DEFAULT_MODEL: {DEFAULT_MODEL}")
        
        # 测试简单的API调用
        print("\n开始测试API调用...")
        response = await litellm.acompletion(
            api_key=API_KEY,
            base_url=API_URL,
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": "你好，请简单介绍一下你自己。"}],
            temperature=0.7,
            max_tokens=100,
            stream=False
        )
        
        print("✓ API调用成功!")
        print(f"响应内容: {response.choices[0].message.content}")
        print(f"Token使用: {response.usage.total_tokens if hasattr(response, 'usage') else '未知'}")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_litellm())