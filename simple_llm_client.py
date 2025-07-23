"""简化的LiteLLM客户端，专门用于request-tester"""

import json
import time
import random
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import litellm


@dataclass
class TextPrompt:
    """文本提示"""
    text: str


@dataclass 
class TextResult:
    """文本结果"""
    text: str


class SimpleLiteLLMClient:
    """简化的LiteLLM客户端"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_retries: int = 2
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.max_retries = max_retries
    
    def generate(
        self,
        messages: List[List[TextPrompt]],
        max_tokens: int,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> tuple[List[TextResult], Dict[str, Any]]:
        """生成响应"""
        
        # 转换消息格式
        litellm_messages = []
        
        if system_prompt:
            litellm_messages.append({"role": "system", "content": system_prompt})
        
        for message_list in messages:
            for message in message_list:
                if isinstance(message, TextPrompt):
                    litellm_messages.append({
                        "role": "user",
                        "content": message.text
                    })
        
        # 重试机制
        response = None
        for retry in range(self.max_retries):
            try:
                # 为模型名称添加openai/前缀
                model_with_prefix = f"openai/{self.model_name}" if not self.model_name.startswith("openai/") else self.model_name
                
                response = litellm.completion(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=model_with_prefix,
                    messages=litellm_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )
                break
            except Exception as e:
                if retry == self.max_retries - 1:
                    print(f"LiteLLM请求失败，重试{retry + 1}次后仍然失败")
                    raise e
                print(f"LiteLLM请求失败，正在重试: {retry + 1}/{self.max_retries}")
                time.sleep(5 * random.uniform(0.8, 1.2))
        
        # 处理响应
        if not response:
            raise Exception("未收到响应")
        
        # 提取内容
        content = ""
        if response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            if hasattr(message, 'content') and message.content:
                content = message.content
        
        # 构建结果
        results = [TextResult(text=content)] if content else []
        
        # 构建元数据
        metadata = {
            "raw_response": response,
            "input_tokens": getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') else 0,
            "output_tokens": getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') else 0,
        }
        
        return results, metadata