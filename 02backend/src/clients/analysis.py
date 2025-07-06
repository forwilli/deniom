"""
AI 分析客户端
"""
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt
import json
import re
import os

from ..core.config import settings
from google import genai
from google.genai import types

class AnalysisClient:
    def __init__(self):
        # 配置代理（通过环境变量）
        if settings.https_proxy:
            print(f">>> [DEBUG] 配置代理设置: {settings.https_proxy}")
            os.environ['HTTPS_PROXY'] = settings.https_proxy
            os.environ['HTTP_PROXY'] = settings.https_proxy
        else:
            print(">>> [DEBUG] 未发现代理配置，使用直连模式")
        
        # 创建客户端（简化版本，让库自动使用环境变量）
        self.client = genai.Client(api_key=settings.gemini_api_key)
        
        print(f">>> [DEBUG] Gemini 客户端配置完成")
        self.semaphore = asyncio.Semaphore(10)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(2))
    async def _generate(self, prompt: str, model_name: str):
        async with self.semaphore:
            print(f">>> [DEBUG] 开始调用 Gemini API...")
            try:
                # 设置超时并简化调用
                response = await asyncio.wait_for(
                    self.client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.7,
                            max_output_tokens=8192,
                            thinking_config=types.ThinkingConfig(thinking_budget=1000)  # 限制thinking tokens
                        )
                    ),
                    timeout=30.0  # 30秒超时
                )
                print(f">>> [DEBUG] Gemini API 调用成功")
                
                # 调试响应内容
                response_text = response.text
                print(f">>> [DEBUG] 响应长度: {len(response_text) if response_text else 'None'}")
                if response_text:
                    print(f">>> [DEBUG] 响应前100字符: {response_text[:100]}")
                else:
                    print(f">>> [DEBUG] 响应为空，完整响应对象: {response}")
                    print(f">>> [DEBUG] 响应候选数量: {len(response.candidates) if hasattr(response, 'candidates') else 'None'}")
                    if hasattr(response, 'candidates') and response.candidates:
                        print(f">>> [DEBUG] 第一个候选内容: {response.candidates[0].content if response.candidates[0].content else 'None'}")
                
                return response_text
            except asyncio.TimeoutError:
                print(f">>> [DEBUG] Gemini API 调用超时")
                raise
            except Exception as e:
                print(f">>> [DEBUG] Gemini API 调用出错: {e}")
                raise

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(2))
    async def _generate_with_search_vertex(self, prompt: str, model_name: str):
        """
        使用Vertex AI端点的Google搜索功能（更稳定的网络连接）
        """
        async with self.semaphore:
            print(f">>> [DEBUG] 开始调用 Vertex AI Gemini API (带搜索)...")
            
            try:
                # 导入Vertex AI相关库
                import vertexai
                from vertexai.generative_models import GenerativeModel, Tool
                import vertexai.preview.generative_models as preview_generative_models
                
                # 初始化Vertex AI（使用全局端点以获得更好的可用性）
                vertexai.init(project=settings.gemini_project_id or "your-project-id", location="us-central1")
                
                # 创建模型实例
                model = GenerativeModel(model_name)
                
                # 配置Google搜索工具 - 使用Vertex AI的方式
                google_search_tool = Tool.from_google_search_retrieval(
                    google_search_retrieval=preview_generative_models.GoogleSearchRetrieval()
                )
                
                # 生成配置
                generation_config = {
                    "temperature": 0.7,
                    "max_output_tokens": 8192,
                }
                
                # 调用API
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        model.generate_content,
                        prompt,
                        tools=[google_search_tool],
                        generation_config=generation_config
                    ),
                    timeout=120.0  # Vertex AI通常需要更长时间
                )
                
                print(f">>> [DEBUG] Vertex AI Gemini API (带搜索) 调用成功")
                return response.text
                
            except ImportError as e:
                print(f">>> [DEBUG] Vertex AI库未安装: {e}")
                raise ImportError("需要安装 google-cloud-aiplatform: pip install google-cloud-aiplatform")
            except Exception as e:
                print(f">>> [DEBUG] Vertex AI调用失败: {e}")
                raise

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(2))
    async def _generate_with_search(self, prompt: str, model_name: str):
        """
        使用Gemini内置的Google搜索功能生成内容（多重降级策略）
        """
        async with self.semaphore:
            print(f">>> [DEBUG] 开始调用 Gemini API (带搜索)...")
            
            # 方案1：尝试Vertex AI端点
            try:
                print(f">>> [DEBUG] 尝试方案1：Vertex AI端点")
                return await self._generate_with_search_vertex(prompt, model_name)
            except Exception as vertex_error:
                print(f">>> [DEBUG] Vertex AI端点失败: {vertex_error}")
            
            # 为搜索API尝试不同的网络配置
            original_http_proxy = os.environ.get('HTTP_PROXY')
            original_https_proxy = os.environ.get('HTTPS_PROXY')
            
            try:
                # 方案2：尝试直连（不使用代理）
                print(f">>> [DEBUG] 尝试方案2：直连模式（不使用代理）")
                os.environ.pop('HTTP_PROXY', None)
                os.environ.pop('HTTPS_PROXY', None)
                
                # 创建新的客户端（不使用代理）
                direct_client = genai.Client(api_key=settings.gemini_api_key)
                
                # 配置Google搜索工具
                google_search_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )
                
                # 设置超时并简化调用
                response = await asyncio.wait_for(
                    direct_client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            tools=[google_search_tool],
                            temperature=0.7,
                            max_output_tokens=8192,
                            thinking_config=types.ThinkingConfig(thinking_budget=1000)
                        )
                    ),
                    timeout=90.0  # 增加超时时间
                )
                print(f">>> [DEBUG] Gemini API (带搜索) 调用成功 - 直连模式")
                
            except Exception as direct_error:
                print(f">>> [DEBUG] 直连模式失败: {direct_error}")
                
                # 方案3：恢复代理设置，尝试代理模式
                print(f">>> [DEBUG] 尝试方案3：代理模式")
                if original_http_proxy:
                    os.environ['HTTP_PROXY'] = original_http_proxy
                if original_https_proxy:
                    os.environ['HTTPS_PROXY'] = original_https_proxy
                
                try:
                    # 配置Google搜索工具
                    google_search_tool = types.Tool(
                        google_search=types.GoogleSearch()
                    )
                    
                    # 使用原有客户端重试
                    response = await asyncio.wait_for(
                        self.client.aio.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                tools=[google_search_tool],
                                temperature=0.7,
                                max_output_tokens=8192,
                                thinking_config=types.ThinkingConfig(thinking_budget=1000)
                            )
                        ),
                        timeout=90.0
                    )
                    print(f">>> [DEBUG] Gemini API (带搜索) 调用成功 - 代理模式")
                except Exception as proxy_error:
                    print(f">>> [DEBUG] 代理模式也失败: {proxy_error}")
                    # 抛出最后的错误
                    raise proxy_error
            
            finally:
                # 确保恢复原始代理设置
                if original_http_proxy:
                    os.environ['HTTP_PROXY'] = original_http_proxy
                elif 'HTTP_PROXY' in os.environ:
                    del os.environ['HTTP_PROXY']
                    
                if original_https_proxy:
                    os.environ['HTTPS_PROXY'] = original_https_proxy
                elif 'HTTPS_PROXY' in os.environ:
                    del os.environ['HTTPS_PROXY']

            # 调试响应内容
            response_text = response.text
            print(f">>> [DEBUG] 响应长度: {len(response_text) if response_text else 'None'}")
            if response_text:
                print(f">>> [DEBUG] 响应前100字符: {response_text[:100]}")
            
            # 输出搜索元数据（用于调试）
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding = candidate.grounding_metadata
                    if grounding and hasattr(grounding, 'web_search_queries'):
                        print(f">>> [DEBUG] 搜索查询: {grounding.web_search_queries}")
                    if grounding and hasattr(grounding, 'grounding_chunks'):
                        print(f">>> [DEBUG] 搜索结果数量: {len(grounding.grounding_chunks)}")
            
            return response_text

    # 注意：核心分析逻辑已迁移到services/analysis_service.py
    # 这个客户端现在只保留基础的AI调用功能
    
    # 注意：所有分析逻辑已迁移到services/analysis_service.py

    # 以下方法已迁移到services/analysis_service.py
    # 为了避免代码重复，这里不再实现具体逻辑
    
    async def perform_screening_analysis(self, project_data: dict) -> dict:
        """已迁移到services/analysis_service.py"""
        raise NotImplementedError("请使用services.analysis_service.perform_screening_analysis")
    
    async def analyze_core_idea(self, project_data: dict) -> dict:
        """已迁移到services/analysis_service.py"""
        raise NotImplementedError("请使用services.analysis_service.analyze_core_idea")
    
    async def analyze_project_readme(self, repo_name: str, readme_content: str) -> dict:
        """已迁移到services/analysis_service.py"""
        raise NotImplementedError("请使用services.analysis_service.analyze_project_readme")
    
    async def analyze_market(self, project_info: dict) -> dict:
        """已迁移到services/analysis_service.py"""
        raise NotImplementedError("请使用services.analysis_service.analyze_market")


# 注意：建议使用services/analysis_service.py中的analysis_service实例
analysis_client = AnalysisClient()