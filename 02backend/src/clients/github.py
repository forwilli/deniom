"""
GitHub API 客户端
"""
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, RetryError
from datetime import datetime, timedelta
import base64
from typing import Optional

from ..core.config import settings

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {"Authorization": f"token {token}"} if token else {}
        self.base_url = "https://api.github.com"
        self.timeout = 30 # 增加超时

    @retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
    async def _request(self, method: str, url: str, **kwargs):
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            response = await client.request(method, url, **kwargs)
            # 对于搜索API，即使没有结果，422 Unprocessable Entity 也可能出现，需要特别处理
            if response.status_code == 422:
                print(f"Warning: GitHub API returned 422 for {url}. This might mean no results or an issue with the query. Details: {response.text}")
                return response
            response.raise_for_status()
            return response

    async def search_newly_created_repos(self, target_date: datetime, limit: int = 1000) -> list[dict]:
        """
        搜索在指定日期（北京时间）创建的、星标数 > 2 的仓库。
        支持分页，最多可获取1000条记录（GitHub API 限制）。
        """
        # 将北京时间 target_date 转换为 UTC 时间范围
        # 北京时间 2025-06-29 00:00:00 -> UTC 2025-06-28 16:00:00
        utc_start_time = target_date - timedelta(hours=8) 
        # 北京时间 2025-06-29 23:59:59 -> UTC 2025-06-29 15:59:59
        utc_end_time = target_date.replace(hour=23, minute=59, second=59) - timedelta(hours=8)

        start_str = utc_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = utc_end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        query = f"stars:>2 created:{start_str}..{end_str}"
        url = f"{self.base_url}/search/repositories"
        
        all_items = []
        page = 1
        per_page = 100 # GitHub API 每页最大数量
        
        while len(all_items) < limit:
            params = {
                "q": query,
                "sort": "updated", # 按更新时间排序，更有活力
                "order": "desc",
                "per_page": per_page,
                "page": page
            }
            
            try:
                print(f"正在获取第 {page} 页数据...")
                response = await self._request("GET", url, params=params)
                
                if response.status_code == 422:
                    print(f"获取第 {page} 页时 API 返回 422，可能已到达结果末尾。")
                    break
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    print("当前页没有更多项目，停止获取。")
                    break
                
                all_items.extend(items)
                
                # 如果返回的项目数少于请求的每页数量，说明是最后一页
                if len(items) < per_page:
                    print("已到达最后一页。")
                    break

                # 检查是否已达到GitHub的1000条搜索结果限制
                # total_count = data.get('total_count', 0)
                # if len(all_items) >= total_count:
                #     print("已获取所有匹配的项目。")
                #     break

                page += 1

            except RetryError as e:
                print(f"获取第 {page} 页时出错 (重试后失败): {e}")
                break # 出错则中断分页
            except Exception as e:
                print(f"获取第 {page} 页时发生未知错误: {e}")
                break # 出错则中断分页
        
        return all_items[:limit] # 返回不超过 limit 的项目

    async def get_readme_content(self, owner: str, repo: str) -> Optional[str]:
        """获取仓库 README 文件的内容"""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                readme_data = response.json()
                content_base64 = readme_data.get("content")
                
                if content_base64:
                    return base64.b64decode(content_base64).decode("utf-8")
                    
            except httpx.HTTPStatusError as e:
                # 如果是 404，说明没有 README，属于正常情况
                if e.response.status_code == 404:
                    print(f"Warning: No README found for {owner}/{repo}")
                    return None
                # 其他错误则需要记录
                print(f"Error fetching README for {owner}/{repo}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while fetching README for {owner}/{repo}: {e}")
        
        return None

github_client = GitHubClient(token=settings.github_token) 