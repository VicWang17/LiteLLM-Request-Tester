#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版本的request-tester，用于测试litellm调用
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

import litellm
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 导入配置
from config import (
    API_URL, API_KEY, AVAILABLE_MODELS, SYSTEM_PROMPT,
    HOST, PORT, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS,
    MAX_REQUEST_COUNT, REQUEST_TIMEOUT, DEFAULT_MODEL
)

# 创建FastAPI应用
app = FastAPI(title="LLM Request Tester", description="大模型请求测试工具")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 存储测试结果
test_results = {}

class TestRequest(BaseModel):
    """测试请求模型"""
    prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS
    count: int = 1
    session_id: Optional[str] = None

class TestResponse(BaseModel):
    """测试响应模型"""
    success: bool
    session_id: str
    message: str
    results: List[Dict[str, Any]] = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "models": AVAILABLE_MODELS
    })

@app.get("/default-model")
async def get_default_model():
    """获取默认模型"""
    return {"default_model": DEFAULT_MODEL}

@app.get("/config")
async def get_config():
    """获取配置信息"""
    return {
        "models": AVAILABLE_MODELS,
        "default_temperature": DEFAULT_TEMPERATURE,
        "default_max_tokens": DEFAULT_MAX_TOKENS,
        "max_request_count": MAX_REQUEST_COUNT,
        "default_model": DEFAULT_MODEL
    }

async def make_api_request(prompt: str, model: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
    """使用litellm发送API请求"""
    try:
        print(f"发送请求到模型: {model}")
        print(f"API URL: {API_URL}")
        print(f"API Key: {API_KEY[:10]}...")
        
        response = await litellm.acompletion(
            api_key=API_KEY,
            base_url=API_URL,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        print(f"收到响应: {response}")
        
        # 将litellm响应转换为标准格式
        return {
            "choices": [{
                "message": {
                    "content": response.choices[0].message.content,
                    "role": "assistant"
                }
            }],
            "usage": {
                "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') else 0,
                "completion_tokens": getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') else 0,
                "total_tokens": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            }
        }
    except Exception as e:
        print(f"LiteLLM API调用失败: {e}")
        import traceback
        traceback.print_exc()
        raise e

@app.post("/test", response_model=TestResponse)
async def run_test(test_req: TestRequest):
    """运行大模型测试"""
    if test_req.count > MAX_REQUEST_COUNT:
        raise HTTPException(status_code=400, detail=f"请求次数不能超过 {MAX_REQUEST_COUNT} 次")
    
    session_id = test_req.session_id or str(uuid4())
    
    if session_id not in test_results:
        test_results[session_id] = []
    
    results = []
    
    try:
        for i in range(test_req.count):
            print(f"执行第 {i+1}/{test_req.count} 次请求...")
            
            start_time = time.time()
            
            try:
                response = await make_api_request(
                    prompt=test_req.prompt,
                    model=test_req.model,
                    temperature=test_req.temperature,
                    max_tokens=test_req.max_tokens
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # 提取响应内容
                content = ""
                if response.get('choices') and len(response['choices']) > 0:
                    choice = response['choices'][0]
                    if choice.get('message'):
                        content = choice['message'].get('content', '')
                
                # 提取token使用信息
                usage = response.get('usage', {})
                
                result = {
                    "index": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "duration": round(duration, 2),
                    "success": True,
                    "response": content[:200] + "..." if len(content) > 200 else content,
                    "input_tokens": usage.get('prompt_tokens', 0),
                    "output_tokens": usage.get('completion_tokens', 0),
                    "total_tokens": usage.get('total_tokens', 0),
                    "model": test_req.model,
                    "error": None
                }
                
                results.append(result)
                test_results[session_id].append(result)
                print(f"第 {i+1} 次请求成功，用时 {duration:.2f}s")
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                error_result = {
                    "index": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "duration": round(duration, 2),
                    "success": False,
                    "response": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "model": test_req.model,
                    "error": str(e)
                }
                
                results.append(error_result)
                test_results[session_id].append(error_result)
                print(f"第 {i+1} 次请求失败: {e}")
        
        return TestResponse(
            success=True,
            session_id=session_id,
            message=f"成功完成 {test_req.count} 次请求测试",
            results=results
        )
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

@app.get("/results/{session_id}")
async def get_results(session_id: str):
    """获取测试结果"""
    if session_id not in test_results:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"session_id": session_id, "results": test_results[session_id]}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print(f"启动服务器在 http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, reload=True)