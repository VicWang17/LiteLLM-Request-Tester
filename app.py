#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型请求测试工具 - 独立版本
专业的大模型API测试工具，支持批量测试和结果分析
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 导入配置
from config import (
    API_URL, API_KEY, AVAILABLE_MODELS, SYSTEM_PROMPT,
    HOST, PORT, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS,
    MAX_REQUEST_COUNT, REQUEST_TIMEOUT, DEFAULT_MODEL
)

# 导入简化的LiteLLM客户端
from simple_llm_client import SimpleLiteLLMClient, TextPrompt

app = FastAPI(
    title="大模型请求测试工具", 
    description="专业的大模型API测试工具，支持批量测试和结果分析",
    version="1.0.0"
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 存储测试结果的全局变量
test_results: Dict[str, List[Dict[str, Any]]] = {}

class TestRequest(BaseModel):
    """测试请求模型"""
    # 简单模式字段
    prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS
    
    # JSON模式字段
    request_json: Optional[Dict[str, Any]] = None
    
    # 通用字段
    count: int = 1
    session_id: Optional[str] = None
    mode: str = "simple"  # "simple" 或 "json"

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

@app.get("/test-buttons", response_class=HTMLResponse)
async def test_buttons():
    """按钮测试页面"""
    with open("test_buttons.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/debug-test")
async def debug_test():
    """调试测试页面"""
    return FileResponse("debug_test.html")

async def make_api_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """使用SimpleLiteLLMClient发送API请求"""
    try:
        # 创建SimpleLiteLLMClient实例
        client = SimpleLiteLLMClient(
            api_key=API_KEY,
            base_url=API_URL,
            model_name=request_data.get("model")
        )
        
        # 准备消息
        messages = []
        for msg in request_data.get("messages", []):
            if msg.get("role") == "user":
                messages.append([TextPrompt(text=msg.get("content", ""))])
        
        # 调用generate方法
        response, metadata = client.generate(
            messages=messages,
            max_tokens=request_data.get("max_tokens", DEFAULT_MAX_TOKENS),
            temperature=request_data.get("temperature", DEFAULT_TEMPERATURE)
        )
        
        # 将响应转换为标准格式
        content = ""
        if response and len(response) > 0:
            content = response[0].text if hasattr(response[0], 'text') else str(response[0])
        
        return {
            "choices": [{
                "message": {
                    "content": content,
                    "role": "assistant"
                }
            }],
            "usage": {
                "prompt_tokens": metadata.get('input_tokens', 0),
                "completion_tokens": metadata.get('output_tokens', 0),
                "total_tokens": metadata.get('input_tokens', 0) + metadata.get('output_tokens', 0)
            }
        }
    except Exception as e:
        print(f"SimpleLiteLLMClient API调用失败: {e}")
        import traceback
        traceback.print_exc()
        raise e

@app.post("/test", response_model=TestResponse)
async def run_test(test_req: TestRequest):
    """运行大模型测试"""
    # 验证请求次数
    if test_req.count > MAX_REQUEST_COUNT:
        raise HTTPException(status_code=400, detail=f"请求次数不能超过 {MAX_REQUEST_COUNT} 次")
    
    session_id = test_req.session_id or str(uuid4())
    
    # 初始化结果存储
    if session_id not in test_results:
        test_results[session_id] = []
    
    results = []
    
    try:
        # 执行多次请求
        for i in range(test_req.count):
            print(f"执行第 {i+1}/{test_req.count} 次请求...")
            
            start_time = time.time()
            response = None
            
            try:
                if test_req.mode == "json":
                    # JSON模式：直接使用提供的完整请求
                    request_data = test_req.request_json.copy()
                else:
                    # 简单模式：构建基本请求
                    request_data = {
                        "model": test_req.model,
                        "messages": [{"role": "user", "content": test_req.prompt}],
                        "temperature": test_req.temperature,
                        "max_tokens": test_req.max_tokens
                    }
                
                response = await make_api_request(request_data)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # 提取响应内容
                content = None
                tool_calls_summary = None
                
                if response.get('choices') and len(response['choices']) > 0:
                    choice = response['choices'][0]
                    if choice.get('message'):
                        content = choice['message'].get('content', '')
                        
                        # 提取tool_calls信息
                        if choice['message'].get('tool_calls'):
                            tool_names = []
                            for tc in choice['message']['tool_calls']:
                                if tc.get('function', {}).get('name'):
                                    tool_names.append(tc['function']['name'])
                            if tool_names:
                                tool_calls_summary = f"调用工具: {', '.join(tool_names)}"
                
                # 组合摘要信息
                response_summary_parts = []
                if content and content.strip():
                    # 限制content长度避免显示过长
                    content_preview = content.strip()
                    if len(content_preview) > 200:
                        content_preview = content_preview[:200] + "..."
                    response_summary_parts.append(f"内容: {content_preview}")
                
                if tool_calls_summary:
                    response_summary_parts.append(tool_calls_summary)
                
                if not response_summary_parts:
                    response_summary = "无响应内容"
                else:
                    response_summary = " | ".join(response_summary_parts)
                
                # 提取token使用信息
                usage = response.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
                
                result = {
                    "index": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "duration": round(duration, 2),
                    "success": True,
                    "response": response_summary,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "model": request_data.get("model", "unknown"),
                    "error": None,
                    "mode": test_req.mode
                }
                
                if test_req.mode == "json":
                    result["full_response"] = response
                
                results.append(result)
                test_results[session_id].append(result)
                print(f"第 {i+1} 次请求成功，用时 {duration:.2f}s")
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                error_model = "unknown"
                if test_req.mode == "simple":
                    error_model = test_req.model
                elif test_req.request_json:
                    error_model = test_req.request_json.get("model", "unknown")

                error_result = {
                    "index": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "duration": round(duration, 2),
                    "success": False,
                    "response": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "model": error_model,
                    "error": str(e),
                    "mode": test_req.mode
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
        return TestResponse(
            success=False,
            session_id=session_id,
            message=f"测试执行失败: {str(e)}",
            results=results
        )

@app.get("/results/{session_id}")
async def get_results(session_id: str):
    """获取指定会话的测试结果"""
    if session_id not in test_results:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "session_id": session_id,
        "results": test_results[session_id],
        "total_count": len(test_results[session_id]),
        "success_count": len([r for r in test_results[session_id] if r["success"]]),
        "error_count": len([r for r in test_results[session_id] if not r["success"]])
    }

@app.get("/sessions")
async def get_sessions():
    """获取所有测试会话"""
    sessions = []
    for session_id, results in test_results.items():
        sessions.append({
            "session_id": session_id,
            "total_count": len(results),
            "success_count": len([r for r in results if r["success"]]),
            "error_count": len([r for r in results if not r["success"]]),
            "last_update": max([r["timestamp"] for r in results]) if results else None
        })
    
    return {"sessions": sessions}

@app.delete("/results/{session_id}")
async def delete_results(session_id: str):
    """删除指定会话的测试结果"""
    if session_id not in test_results:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    del test_results[session_id]
    return {"message": f"已删除会话 {session_id} 的结果"}

@app.get("/system-prompt")
async def get_system_prompt():
    """获取系统提示词"""
    return {
        "system_prompt": SYSTEM_PROMPT
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "api_url": API_URL,
        "available_models": AVAILABLE_MODELS,
        "active_sessions": len(test_results),
        "version": "1.0.0"
    }

@app.get("/config")
async def get_config():
    """获取当前配置信息"""
    return {
        "api_url": API_URL,
        "available_models": AVAILABLE_MODELS,
        "default_model": DEFAULT_MODEL,
        "default_temperature": DEFAULT_TEMPERATURE,
        "default_max_tokens": DEFAULT_MAX_TOKENS,
        "max_request_count": MAX_REQUEST_COUNT,
        "request_timeout": REQUEST_TIMEOUT
    }

@app.get("/default-model")
async def get_default_model():
    """获取默认模型"""
    return {
        "default_model": DEFAULT_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    print(f"启动 Request Tester v1.0.0")
    print(f"API地址: {API_URL}")
    print(f"支持模型: {len(AVAILABLE_MODELS)} 个")
    print(f"访问地址: http://{HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)