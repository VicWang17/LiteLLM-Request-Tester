#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Tester 独立配置文件
直接修改此文件中的配置项即可
"""

import os
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# =============================================================================
# API 配置（必需修改）
# =============================================================================
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

# 验证必需的环境变量
if not API_URL:
    raise ValueError("API_URL 环境变量未设置。请创建 .env 文件并设置 API_URL")
if not API_KEY:
    raise ValueError("API_KEY 环境变量未设置。请创建 .env 文件并设置 API_KEY")

# =============================================================================
# 应用服务配置
# =============================================================================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8005))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# =============================================================================
# 模型配置
# =============================================================================
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3-coder-plus")

# 支持的模型列表（可添加或删除）
AVAILABLE_MODELS: List[str] = [
    "lm_studio/qwen3-coder-plus",
    "lm_studio/Kimi-K2-Instruct-silflow",
    "lm_studio/Hunyuan-A13B-Instruct",
    "lm_studio/Qwen3-Embedding-4B-silflow",
    "gpt-4o-mini",
    "gpt-4o",
    "qwen-max-latest",
    "claude-3-sonnet",
]

# =============================================================================
# 默认系统提示词
# =============================================================================
SYSTEM_PROMPT = """你是一个智能助手，能够帮助用户解答问题，执行任务，并提供有价值的信息和建议。

你具备以下能力：
1. 回答各种问题，提供准确、有用的信息
2. 协助分析问题和提供解决方案
3. 进行创意思考和头脑风暴
4. 帮助编写、修改和优化文本内容
5. 提供学习建议和知识解释

请以友好、专业的态度为用户服务。"""

# =============================================================================
# API 请求配置
# =============================================================================
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000
MAX_REQUEST_COUNT = 20
REQUEST_TIMEOUT = 300  # 5分钟超时