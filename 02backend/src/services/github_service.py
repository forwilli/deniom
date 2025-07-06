"""
GitHub服务
唯一负责与GitHub API的所有交互
"""
from typing import List, Optional
from datetime import datetime, timedelta
import httpx
from ..core.config import settings


class GitHubService:
    """GitHub API交互服务"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {settings.github_token}" if settings.github_token else ""
        }
    
    async def search_newly_created_repos(
        self, 
        target_date: datetime, 
        limit: int = 50
    ) -> List[dict]:
        """
        搜索指定日期创建的新仓库
        
        Args:
            target_date: 目标日期（北京时间）
            limit: 返回结果数量限制
            
        Returns:
            仓库信息列表
        """
        # 转换为UTC时间范围
        beijing_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        beijing_end = beijing_start + timedelta(days=1)
        
        # 北京时间转UTC (减8小时)
        utc_start = beijing_start - timedelta(hours=8)
        utc_end = beijing_end - timedelta(hours=8)
        
        # 构建搜索查询
        date_range = f"{utc_start.strftime('%Y-%m-%dT%H:%M:%S')}..{utc_end.strftime('%Y-%m-%dT%H:%M:%S')}"
        query = f"created:{date_range} stars:>2"
        
        # 搜索参数
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100)
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search/repositories",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                repos = data.get("items", [])
                
                # 如果需要更多结果，继续请求
                if limit > 100 and data.get("total_count", 0) > 100:
                    # 实现分页逻辑
                    repos.extend(await self._fetch_additional_pages(
                        client, query, limit - 100, page=2
                    ))
                
                return repos[:limit]
                
        except httpx.HTTPError as e:
            print(f"GitHub API 错误: {e}")
            return []
    
    async def get_readme_content(
        self, 
        owner: str, 
        repo_name: str
    ) -> Optional[str]:
        """
        获取仓库的README内容
        
        Args:
            owner: 仓库所有者
            repo_name: 仓库名称
            
        Returns:
            README内容文本，如果不存在则返回None
        """
        readme_paths = ["README.md", "readme.md", "README.MD", "Readme.md", "README", "readme"]
        
        async with httpx.AsyncClient() as client:
            for readme_path in readme_paths:
                try:
                    response = await client.get(
                        f"{self.base_url}/repos/{owner}/{repo_name}/contents/{readme_path}",
                        headers=self.headers,
                        timeout=20.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # 解码Base64内容
                        if data.get("encoding") == "base64":
                            import base64
                            content_bytes = base64.b64decode(data["content"])
                            return content_bytes.decode("utf-8")
                        else:
                            return data.get("content", "")
                            
                except httpx.HTTPError:
                    continue
        
        return None
    
    async def get_repository_info(
        self, 
        owner: str, 
        repo_name: str
    ) -> Optional[dict]:
        """
        获取仓库详细信息
        
        Args:
            owner: 仓库所有者
            repo_name: 仓库名称
            
        Returns:
            仓库信息字典
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo_name}",
                    headers=self.headers,
                    timeout=20.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            print(f"获取仓库信息失败 {owner}/{repo_name}: {e}")
            return None
    
    async def get_repository_languages(
        self, 
        owner: str, 
        repo_name: str
    ) -> dict:
        """
        获取仓库使用的编程语言统计
        
        Args:
            owner: 仓库所有者
            repo_name: 仓库名称
            
        Returns:
            语言使用统计字典
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo_name}/languages",
                    headers=self.headers,
                    timeout=20.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError:
            return {}
    
    async def _fetch_additional_pages(
        self, 
        client: httpx.AsyncClient, 
        query: str, 
        remaining: int, 
        page: int
    ) -> List[dict]:
        """
        获取额外的搜索结果页面
        
        Args:
            client: HTTP客户端
            query: 搜索查询
            remaining: 剩余需要获取的数量
            page: 当前页码
            
        Returns:
            额外的仓库列表
        """
        results = []
        
        while remaining > 0 and page <= 10:  # GitHub API限制最多1000个结果
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(remaining, 100),
                "page": page
            }
            
            try:
                response = await client.get(
                    f"{self.base_url}/search/repositories",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break
                
                results.extend(items)
                remaining -= len(items)
                page += 1
                
            except httpx.HTTPError:
                break
        
        return results


# 创建服务实例供其他模块使用
github_service = GitHubService()