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

import litellm
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
    """直接使用LiteLLM发送完整的API请求"""
    try:
        print(f"发送完整请求到LiteLLM: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        # 为模型名称添加openai/前缀（如果需要）
        model = request_data.get("model", DEFAULT_MODEL)
        if not model.startswith("openai/"):
            model = f"openai/{model}"
        
        # 准备LiteLLM请求参数
        litellm_params = {
            "api_key": API_KEY,
            "base_url": API_URL,
            "model": model,
            **request_data  # 传递所有原始请求数据
        }
        
        # 强制禁用流式传输以获得完整响应
        litellm_params["stream"] = False
        
        # 移除可能冲突的参数
        litellm_params.pop("model", None)  # 避免重复
        
        # 重新设置model参数
        litellm_params["model"] = model
        
        print(f"LiteLLM请求参数: {json.dumps({k: v for k, v in litellm_params.items() if k != 'api_key'}, indent=2, ensure_ascii=False)}")
        
        # 使用LiteLLM直接发送请求
        import litellm
        response = await litellm.acompletion(**litellm_params)
        
        print(f"LiteLLM响应类型: {type(response)}")
        print(f"LiteLLM响应对象属性: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # 检查是否是CustomStreamWrapper对象
        if hasattr(response, '__class__') and 'CustomStreamWrapper' in str(response.__class__):
            print("检测到CustomStreamWrapper对象，使用原始响应")
            print(f"使用原始响应: {response}")
            
            # 对于CustomStreamWrapper，我们需要特殊处理
            response_dict = {
                'model': getattr(response, 'model', 'unknown'),
                'choices': [],
                'usage': {}
            }
            
            # 尝试提取其他字段
            if hasattr(response, 'id'):
                response_dict['id'] = response.id
            if hasattr(response, 'object'):
                response_dict['object'] = response.object
            if hasattr(response, 'created'):
                response_dict['created'] = response.created
            if hasattr(response, 'system_fingerprint'):
                response_dict['system_fingerprint'] = response.system_fingerprint
                
            # 对于流式响应，尝试从complete_response或response_uptil_now获取数据
            complete_response = None
            print(f"检查complete_response: {hasattr(response, 'complete_response')}")
            if hasattr(response, 'complete_response'):
                print(f"complete_response值: {response.complete_response}")
                if response.complete_response:
                    complete_response = response.complete_response
                    print(f"找到complete_response: {type(complete_response)}")
            
            print(f"检查response_uptil_now: {hasattr(response, 'response_uptil_now')}")
            if hasattr(response, 'response_uptil_now'):
                print(f"response_uptil_now值: {response.response_uptil_now}")
                if not complete_response and response.response_uptil_now:
                    complete_response = response.response_uptil_now
                    print(f"找到response_uptil_now: {type(complete_response)}")
            
            # 检查其他可能的属性
            print(f"检查chunks: {hasattr(response, 'chunks')}")
            if hasattr(response, 'chunks'):
                print(f"chunks值: {response.chunks}")
            
            print(f"检查choices直接访问: {hasattr(response, 'choices')}")
            if hasattr(response, 'choices'):
                print(f"choices值: {response.choices}")
            
            print(f"检查usage直接访问: {hasattr(response, 'usage')}")
            if hasattr(response, 'usage'):
                print(f"usage值: {response.usage}")
            
            if complete_response:
                # 从完整响应中提取数据
                if hasattr(complete_response, 'choices') and complete_response.choices:
                    response_dict['choices'] = []
                    for choice in complete_response.choices:
                        choice_dict = {}
                        if hasattr(choice, 'index'):
                            choice_dict['index'] = choice.index
                        if hasattr(choice, 'finish_reason'):
                            choice_dict['finish_reason'] = choice.finish_reason
                            
                        # 提取message
                        if hasattr(choice, 'message'):
                            message_dict = {}
                            if hasattr(choice.message, 'role'):
                                message_dict['role'] = choice.message.role
                            if hasattr(choice.message, 'content'):
                                message_dict['content'] = choice.message.content
                            if hasattr(choice.message, 'tool_calls'):
                                message_dict['tool_calls'] = choice.message.tool_calls
                            if hasattr(choice.message, 'function_call'):
                                message_dict['function_call'] = choice.message.function_call
                            choice_dict['message'] = message_dict
                            
                        response_dict['choices'].append(choice_dict)
                
                # 提取usage
                if hasattr(complete_response, 'usage') and complete_response.usage:
                    usage_dict = {}
                    if hasattr(complete_response.usage, 'prompt_tokens'):
                        usage_dict['prompt_tokens'] = complete_response.usage.prompt_tokens
                    if hasattr(complete_response.usage, 'completion_tokens'):
                        usage_dict['completion_tokens'] = complete_response.usage.completion_tokens
                    if hasattr(complete_response.usage, 'total_tokens'):
                        usage_dict['total_tokens'] = complete_response.usage.total_tokens
                    if hasattr(complete_response.usage, 'prompt_tokens_details'):
                        usage_dict['prompt_tokens_details'] = complete_response.usage.prompt_tokens_details
                    if hasattr(complete_response.usage, 'completion_tokens_details'):
                        usage_dict['completion_tokens_details'] = complete_response.usage.completion_tokens_details
                    response_dict['usage'] = usage_dict
            else:
                # 如果没有complete_response，尝试直接从response对象提取
                if hasattr(response, 'choices') and response.choices:
                    response_dict['choices'] = []
                    for choice in response.choices:
                        choice_dict = {}
                        if hasattr(choice, 'index'):
                            choice_dict['index'] = choice.index
                        if hasattr(choice, 'finish_reason'):
                            choice_dict['finish_reason'] = choice.finish_reason
                            
                        # 提取message
                        if hasattr(choice, 'message'):
                            message_dict = {}
                            if hasattr(choice.message, 'role'):
                                message_dict['role'] = choice.message.role
                            if hasattr(choice.message, 'content'):
                                message_dict['content'] = choice.message.content
                            if hasattr(choice.message, 'tool_calls'):
                                message_dict['tool_calls'] = choice.message.tool_calls
                            if hasattr(choice.message, 'function_call'):
                                message_dict['function_call'] = choice.message.function_call
                            choice_dict['message'] = message_dict
                            
                        response_dict['choices'].append(choice_dict)
                
                # 提取usage
                if hasattr(response, 'usage') and response.usage:
                    usage_dict = {}
                    if hasattr(response.usage, 'prompt_tokens'):
                        usage_dict['prompt_tokens'] = response.usage.prompt_tokens
                    if hasattr(response.usage, 'completion_tokens'):
                        usage_dict['completion_tokens'] = response.usage.completion_tokens
                    if hasattr(response.usage, 'total_tokens'):
                        usage_dict['total_tokens'] = response.usage.total_tokens
                    if hasattr(response.usage, 'prompt_tokens_details'):
                        usage_dict['prompt_tokens_details'] = response.usage.prompt_tokens_details
                    if hasattr(response.usage, 'completion_tokens_details'):
                        usage_dict['completion_tokens_details'] = response.usage.completion_tokens_details
                    response_dict['usage'] = usage_dict
        else:
            # 安全地提取响应数据，避免序列化问题
            response_dict = {}
            
            # 提取基本字段
            if hasattr(response, 'id'):
                response_dict['id'] = response.id
            if hasattr(response, 'object'):
                response_dict['object'] = response.object
            if hasattr(response, 'created'):
                response_dict['created'] = response.created
            if hasattr(response, 'model'):
                response_dict['model'] = response.model
            if hasattr(response, 'system_fingerprint'):
                response_dict['system_fingerprint'] = response.system_fingerprint
                
            # 提取choices
            if hasattr(response, 'choices') and response.choices:
                response_dict['choices'] = []
                for choice in response.choices:
                    choice_dict = {}
                    if hasattr(choice, 'index'):
                        choice_dict['index'] = choice.index
                    if hasattr(choice, 'finish_reason'):
                        choice_dict['finish_reason'] = choice.finish_reason
                        
                    # 提取message
                    if hasattr(choice, 'message'):
                        message_dict = {}
                        if hasattr(choice.message, 'role'):
                            message_dict['role'] = choice.message.role
                        if hasattr(choice.message, 'content'):
                            message_dict['content'] = choice.message.content
                        if hasattr(choice.message, 'tool_calls'):
                            message_dict['tool_calls'] = choice.message.tool_calls
                        if hasattr(choice.message, 'function_call'):
                            message_dict['function_call'] = choice.message.function_call
                        choice_dict['message'] = message_dict
                        
                    response_dict['choices'].append(choice_dict)
            
            # 提取usage
            if hasattr(response, 'usage') and response.usage:
                usage_dict = {}
                if hasattr(response.usage, 'prompt_tokens'):
                    usage_dict['prompt_tokens'] = response.usage.prompt_tokens
                if hasattr(response.usage, 'completion_tokens'):
                    usage_dict['completion_tokens'] = response.usage.completion_tokens
                if hasattr(response.usage, 'total_tokens'):
                    usage_dict['total_tokens'] = response.usage.total_tokens
                if hasattr(response.usage, 'prompt_tokens_details'):
                    usage_dict['prompt_tokens_details'] = response.usage.prompt_tokens_details
                if hasattr(response.usage, 'completion_tokens_details'):
                    usage_dict['completion_tokens_details'] = response.usage.completion_tokens_details
                response_dict['usage'] = usage_dict
        
        print(f"最终提取的响应字典: {json.dumps(response_dict, indent=2, ensure_ascii=False, default=str)}")
        
        return response_dict
    except Exception as e:
        print(f"LiteLLM API调用失败: {e}")
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
                tool_calls_info = None
                full_content = None
                
                if response.get('choices') and len(response['choices']) > 0:
                    choice = response['choices'][0]
                    if choice.get('message'):
                        full_content = choice['message'].get('content', '')
                        content = full_content
                        
                        # 提取tool_calls信息
                        if choice['message'].get('tool_calls'):
                            tool_calls_list = []
                            for tc in choice['message']['tool_calls']:
                                tool_info = {}
                                if tc.get('function', {}).get('name'):
                                    tool_info['name'] = tc['function']['name']
                                if tc.get('function', {}).get('arguments'):
                                    try:
                                        import json
                                        args = json.loads(tc['function']['arguments'])
                                        tool_info['arguments'] = args
                                    except:
                                        tool_info['arguments'] = tc['function']['arguments']
                                if tc.get('id'):
                                    tool_info['id'] = tc['id']
                                tool_calls_list.append(tool_info)
                            
                            if tool_calls_list:
                                tool_calls_info = tool_calls_list
                
                # 构建响应摘要
                response_data = {
                    'content': content,
                    'tool_calls': tool_calls_info,
                    'full_content': full_content
                }
                
                # 为了向后兼容，仍然生成response字段
                response_summary_parts = []
                if content and content.strip():
                    # 限制content长度避免显示过长
                    content_preview = content.strip()
                    if len(content_preview) > 200:
                        content_preview = content_preview[:200] + "..."
                    response_summary_parts.append(f"内容: {content_preview}")
                
                if tool_calls_info:
                    tool_names = [tc.get('name', '未知工具') for tc in tool_calls_info]
                    response_summary_parts.append(f"调用工具: {', '.join(tool_names)}")
                
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
                    "content": response_data.get('content'),
                    "tool_calls": response_data.get('tool_calls'),
                    "full_content": response_data.get('full_content'),
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
    
    results = test_results[session_id]
    total_count = len(results)
    success_count = len([r for r in results if r["success"]])
    error_count = len([r for r in results if not r["success"]])
    
    # 计算工具调用统计
    tool_call_count = 0
    total_tool_calls = 0
    
    for result in results:
        if result["success"] and result.get("tool_calls"):
            tool_call_count += 1
            if isinstance(result["tool_calls"], list):
                total_tool_calls += len(result["tool_calls"])
            else:
                total_tool_calls += 1
    
    tool_call_probability = (tool_call_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "session_id": session_id,
        "results": results,
        "total_count": total_count,
        "success_count": success_count,
        "error_count": error_count,
        "tool_call_count": tool_call_count,
        "total_tool_calls": total_tool_calls,
        "tool_call_probability": round(tool_call_probability, 1)
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