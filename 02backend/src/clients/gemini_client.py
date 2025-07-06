"""
Gemini API Client

This module provides a configured and ready-to-use client for interacting
with the Google Gemini API. It handles API key configuration and sets up
the generative model based on the project's settings.
"""

import google.generativeai as genai
from app.core.config import settings
import logging
import os
import httpx

# This variable will hold our model instance.
gemini_model_instance = None

try:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
    
    # 配置代理（如果设置了）
    if settings.http_proxy or settings.https_proxy:
        proxies = {}
        if settings.http_proxy:
            proxies['http'] = settings.http_proxy
            os.environ['HTTP_PROXY'] = settings.http_proxy
        if settings.https_proxy:
            proxies['https'] = settings.https_proxy
            os.environ['HTTPS_PROXY'] = settings.https_proxy
        
        logging.info(f"🌐 Using proxy configuration: {proxies}")
    
    genai.configure(api_key=settings.gemini_api_key)
    
    generation_config = {
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,  # 减少输出长度以提高响应速度
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    gemini_model_instance = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    logging.info(f"✅ Gemini client configured successfully for model: {settings.gemini_model}")

except (ValueError, Exception) as e:
    logging.warning(f"⚠️ Gemini client could not be configured: {e}")
    logging.warning("AI analysis features will be disabled. Please check your GEMINI_API_KEY.")
    gemini_model_instance = None 