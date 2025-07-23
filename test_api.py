#!/usr/bin/env python3
"""测试request-tester服务的API"""

import requests
import json

def test_api():
    """测试API"""
    url = "http://localhost:8005/test"
    
    # 测试数据
    test_data = {
        "prompt": "你好，请介绍一下你自己",
        "model": "qwen3-coder-plus",
        "temperature": 0.7,
        "max_tokens": 100,
        "count": 1,
        "mode": "simple"
    }
    
    print("发送测试请求...")
    print(f"URL: {url}")
    print(f"数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("测试成功!")
            print(f"会话ID: {result.get('session_id')}")
            print(f"消息: {result.get('message')}")
            if result.get('results'):
                for r in result['results']:
                    print(f"结果 {r.get('index')}: {r.get('response')}")
        else:
            print(f"测试失败: {response.status_code}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_api()