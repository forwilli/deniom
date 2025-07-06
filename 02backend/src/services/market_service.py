"""
市场服务
唯一负责执行外部网络搜索
"""
from typing import List, Optional
import httpx
from ..core.config import settings


class MarketService:
    """市场研究服务 - 负责外部市场信息搜索"""
    
    def __init__(self):
        self.serper_api_key = settings.serper_api_key
        self.serper_url = "https://google.serper.dev/search"
    
    async def search_market_info(
        self, 
        query: str, 
        num_results: int = 5
    ) -> Optional[str]:
        """
        使用Serper API执行市场信息搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            格式化的搜索结果文本，如果失败返回None
        """
        if not self.serper_api_key:
            print("Serper API密钥未配置，跳过网络搜索")
            return None
        
        try:
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": num_results,
                "hl": "en"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.serper_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                return self._format_search_results(data, num_results)
                
        except Exception as e:
            print(f"Serper搜索失败: {e}")
            return None
    
    async def search_competitors(
        self, 
        project_name: str, 
        description: str, 
        language: str
    ) -> List[str]:
        """
        搜索项目的竞争对手信息
        
        Args:
            project_name: 项目名称
            description: 项目描述
            language: 编程语言
            
        Returns:
            搜索结果列表
        """
        queries = [
            f"{project_name} {language} competitors alternatives",
            f"{project_name} similar projects",
            f"{description} market analysis 2024"
        ]
        
        results = []
        for query in queries[:2]:  # 限制搜索次数
            search_result = await self.search_market_info(query)
            if search_result:
                results.append(f"搜索查询: {query}\n{search_result}")
        
        return results
    
    async def search_market_trends(
        self, 
        technology: str, 
        domain: str
    ) -> Optional[str]:
        """
        搜索技术和领域的市场趋势
        
        Args:
            technology: 技术栈
            domain: 应用领域
            
        Returns:
            市场趋势信息
        """
        query = f"{technology} {domain} market trends 2024 growth"
        return await self.search_market_info(query, num_results=10)
    
    async def search_investment_activity(
        self, 
        domain: str
    ) -> Optional[str]:
        """
        搜索相关领域的投资活动
        
        Args:
            domain: 应用领域
            
        Returns:
            投资活动信息
        """
        query = f"{domain} startup funding investment 2024"
        return await self.search_market_info(query, num_results=5)
    
    def _format_search_results(
        self, 
        data: dict, 
        num_results: int
    ) -> str:
        """
        格式化搜索结果
        
        Args:
            data: Serper API返回的数据
            num_results: 期望的结果数量
            
        Returns:
            格式化后的文本
        """
        results = []
        
        # 提取有机搜索结果
        if "organic" in data:
            for item in data["organic"][:num_results]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                results.append(f"**{title}**\n{snippet}\n来源: {link}\n")
        
        # 提取知识面板信息
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            if "title" in kg:
                results.append(f"**知识图谱: {kg['title']}**\n{kg.get('description', '')}\n")
        
        # 提取相关问题
        if "peopleAlsoAsk" in data:
            questions = []
            for qa in data["peopleAlsoAsk"][:3]:
                question = qa.get("question", "")
                answer = qa.get("snippet", "")
                questions.append(f"Q: {question}\nA: {answer}")
            
            if questions:
                results.append("**相关问题**:\n" + "\n\n".join(questions))
        
        search_results = "\n".join(results)
        print(f"Serper搜索成功，获得{len(results)}个结果")
        
        return search_results


# 创建服务实例供其他模块使用
market_service = MarketService()