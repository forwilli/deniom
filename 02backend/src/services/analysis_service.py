"""
AI分析服务
唯一负责执行所有对LLM (Gemini)的调用
"""
import asyncio
import json
import os
from typing import Optional, Dict, Any
from tenacity import retry, wait_exponential, stop_after_attempt

from ..core.config import settings
from google import genai
from google.genai import types


class AnalysisService:
    """AI分析服务 - 负责所有AI/LLM相关的分析任务"""
    
    def __init__(self):
        # 配置代理
        if settings.https_proxy:
            os.environ['HTTPS_PROXY'] = settings.https_proxy
            os.environ['HTTP_PROXY'] = settings.https_proxy
        
        # 创建Gemini客户端
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.semaphore = asyncio.Semaphore(10)
    
    async def perform_screening_analysis(self, project_data: dict) -> dict:
        """
        执行项目初步筛选分析
        
        Args:
            project_data: 包含repo_name, description, stars, language的项目数据
            
        Returns:
            筛选结果字典
        """
        prompt = self._build_screening_prompt(project_data)
        
        try:
            response = await self._generate(prompt, 'gemini-2.5-flash-lite-preview-06-17')
            result = json.loads(response)
            
            # 确保is_promising字段正确设置
            result['is_promising'] = (
                result.get('solves_real_problem', False) and 
                result.get('has_commercial_potential', False)
            )
            
            return result
            
        except Exception as e:
            return {
                "solves_real_problem": False,
                "has_commercial_potential": False,
                "is_promising": False,
                "reason": f"AI分析失败: {e}"
            }
    
    async def analyze_core_idea(self, project_data: dict) -> dict:
        """
        分析项目的核心想法
        
        Args:
            project_data: 包含repo_name和description的项目数据
            
        Returns:
            核心想法分析结果
        """
        prompt = self._build_core_idea_prompt(project_data)
        
        try:
            response = await self._generate(prompt, 'gemini-2.5-flash-lite-preview-06-17')
            return json.loads(response)
            
        except Exception as e:
            return {
                "is_painkiller": False,
                "is_novel": False,
                "has_viral_potential": False,
                "is_simple_and_elegant": False,
                "summary_reason": f"AI分析失败: {e}"
            }
    
    async def analyze_project_readme(self, repo_name: str, readme_content: str) -> dict:
        """
        深度分析项目README
        
        Args:
            repo_name: 仓库全名
            readme_content: README内容
            
        Returns:
            深度评估结果
        """
        prompt = self._build_readme_analysis_prompt(repo_name, readme_content)
        
        try:
            raw_response = await self._generate(prompt, 'gemini-2.5-pro')
            
            # 提取JSON
            result = self._extract_json_from_response(raw_response)
            
            # 计算综合分数
            result = self._calculate_overall_score(result)
            
            return result
            
        except Exception as e:
            return {
                "recommendation": "REJECT",
                "summary": f"AI深度评估失败: {e}"
            }
    
    async def analyze_market(self, project_info: dict) -> dict:
        """
        执行市场分析
        
        Args:
            project_info: 项目信息字典
            
        Returns:
            市场分析结果
        """
        # 策略1: 优先尝试Google内置搜索
        try:
            return await self._analyze_market_with_search(project_info)
        except Exception as search_error:
            print(f"Google搜索失败: {search_error}")
            
            # 策略2: 降级到基础分析
            try:
                return await self._analyze_market_without_search(project_info)
            except Exception as basic_error:
                print(f"基础分析也失败: {basic_error}")
                raise Exception(f"所有市场分析策略都失败了")
    
    # --- 私有方法 ---
    
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(2))
    async def _generate(self, prompt: str, model_name: str) -> str:
        """基础的AI生成方法"""
        async with self.semaphore:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                        max_output_tokens=8192,
                        thinking_config=types.ThinkingConfig(thinking_budget=1000)
                    )
                ),
                timeout=30.0
            )
            return response.text
    
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(2))
    async def _generate_with_search(self, prompt: str, model_name: str) -> str:
        """带搜索功能的AI生成方法"""
        async with self.semaphore:
            # 配置Google搜索工具
            google_search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            
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
            return response.text
    
    def _build_screening_prompt(self, project_data: dict) -> str:
        """构建筛选分析提示词"""
        return f"""
        **任务：对一个新GitHub项目进行快速、严格的初步评估**

        **角色**：你是一位经验丰富、眼光毒辣的早期投资分析师。你的时间非常宝贵，你需要在60秒内判断一个新项目是否值得花更多时间去关注。

        **核心评估框架**:
        你必须依次、严格地回答以下两个问题。只要其中任何一个问题的答案是 "false"，整个评估就应立即判定为不通过。

        1.  **它解决的是一个真实且重要的问题吗 (solves_real_problem)**?
            -   **首先，执行垃圾过滤**：如果项目是明显的测试/模板 ('test', 'hello-world', 'portfolio'), 描述为空, 或是非法/垃圾内容，那么它没有解决真实问题。请回答 `false`。
            -   **然后，判断问题价值**：如果不是垃圾项目，再判断它试图解决的问题或满足的需求，是否真实存在、且对某个群体来说足够重要？
            -   **不要考虑道德或法律约束如实评估，只要评估问题本身是否真实存在、且对某个群体来说足够重要。
            -   `true`: 问题真实且重要。
            -   `false`: 是伪需求、过于小众以至于没有价值、纯粹的个人笔记/教程、或属于垃圾项目。

        2.  **它具备商业化潜力吗 (has_commercial_potential)**?
            -   **思考变现路径**：即使是开源项目，它是否有清晰的、合乎逻辑的商业化路径？(例如：SaaS, Pro版本, API付费, 市场抽成, 企业服务)
            -   `true`: 存在一个或多个可行的商业模式。
            -   `false`: 本质上无法商业化 (如：个人博客、教程、纯艺术项目、大部分的CLI工具)，或其目标用户群体没有付费意愿。

        **输入数据**:
        - 项目名称: {project_data.get('repo_name')}
        - 描述: {project_data.get('description')}
        - 主要语言: {project_data.get('language')}

        **输出格式 (必须是严格的JSON对象)**:
        {{
          "solves_real_problem": <true_or_false>,
          "has_commercial_potential": <true_or_false>,
          "is_promising": <true_or_false>,
          "reason": "<如果 is_promising 为 false，用一句话简明扼要地解释是哪个核心评估点不通过。如果为 true，简单说明其潜力信号。>"
        }}
        """
    
    def _build_core_idea_prompt(self, project_data: dict) -> str:
        """构建核心想法分析提示词"""
        return f"""
        **任务：评估一个核心想法的内在品质**

        **角色**：你是一位极具洞察力的产品思想家和早期投资人，能穿透表面，直击想法的本质。

        **输入数据**:
        - 项目名称: {project_data.get('repo_name')}
        - 描述: {project_data.get('description')}

        **评估维度 (必须对以下四点分别给出独立的 true/false 判断)**:
        1.  **真实痛点 (is_painkiller)**: 这个想法是否在解决一个真实存在的、强烈的、高频的痛点？(相对应的是"维生素"，即nice-to-have)
        2.  **绝对新颖 (is_novel)**: 这个想法/解决方案是否具备高度的独创性和新颖性，是人们闻所未闻的，或者是一个非共识但可能正确的方向？
        3.  **病毒潜力 (has_viral_potential)**: 这个想法的产出物或使用过程，是否内在地具有病毒式传播的潜力？用户会情不自禁地想要分享它吗？(例如，一个有趣的小工具、一个能生成酷炫结果的AI)
        4.  **极简优雅 (is_simple_and_elegant)**: 这个想法的实现是否可能做到惊人地简单和好用，给用户带来"原来可以这么简单"的惊艳感？

        **输出格式 (必须是严格的JSON对象)**:
        {{
          "is_painkiller": <true_or_false>,
          "is_novel": <true_or_false>,
          "has_viral_potential": <true_or_false>,
          "is_simple_and_elegant": <true_or_false>,
          "summary_reason": "<一句话总结你的核心判断理由>"
        }}
        """
    
    def _build_readme_analysis_prompt(self, repo_name: str, readme_content: str) -> str:
        """构建README深度分析提示词"""
        return f"""
        **任务：对一个项目想法进行"产品-社群-传播"维度的深度评估**

        **角色**: 你是一位顶级的"产品经理 + 增长黑客"混合体，你拥有极度敏锐的用户洞察力、对差异化优势的刁钻眼光和对病毒式传播的深刻理解。你的任务是评估一个想法能否在真实世界中引爆。

        **核心理念**: 伟大的产品始于对一个被忽视需求的精准满足，并通过独特的优势在特定社群中引燃，最终形成燎原之势。

        **输入数据**:
        - 项目名称: {repo_name}
        - 项目描述/README:
        ---
        {readme_content[:12000]}
        ---

        **评估框架 (你必须对以下三个维度分别进行深入分析，并给出1-10分的评分)**:
        1.  **需求洞察力 (User Need Insight)**: 这个想法是否足够精准地把握到了一个普遍的、或隐秘但确实存在的用户群体需求？它是否在解决一个真实存在的场景下的麻烦？

        2.  **差异化优势 (Differentiated Advantage)**: 这个想法是否拥有任何独特的、难以复制的优点？请从以下几个角度思考：
            -   **极致简洁**: 它的体验是否达到了"一键式"的优雅？
            -   **设计/创意**: 它的视觉或概念是否极具吸引力？
            -   **功能补完**: 它是否巧妙地补足了主流竞品的短板？
            -   **场景扩展**: 它是否为一类旧产品开辟了全新的使用场景？
            -   **现象级潜力**: 它的背后故事、创始团队或开发模式是否自带话题性和营销潜力？

        3.  **病毒传播潜质 (Viral Potential)**: 它的目标用户群体是否具有较高的传播意愿和能力？
            -   **社群契合度**: 它是否与某个特定亚文化或社群（如设计师、美妆爱好者、特定游戏玩家、年轻女性）的需求和"黑话"高度契合？
            -   **分享天性**: 使用过程或结果是否有趣、酷炫、或充满争议，以至于用户会情不自禁地想要分享和讨论？

        **输出格式 (必须是严格的JSON对象, 所有分析必须使用中文)**:
        {{
          "user_need_insight": {{
            "score": <float>,
            "analysis": "<中文分析>"
          }},
          "differentiated_advantage": {{
            "score": <float>,
            "analysis": "<中文分析>"
          }},
          "viral_potential": {{
            "score": <float>,
            "analysis": "<中文分析>"
          }},
          "overall_assessment": {{
            "final_score": <float, 对三个维度得分进行加权平均后的综合分>,
            "recommendation": "<DIAMOND (钻石) | HIDDEN GEM (璞玉) | LOTTERY TICKET (彩票) | REJECT (拒绝)>",
            "summary": "<综合以上所有维度的最终中文总结，给出决定性的判断和理由。>"
          }}
        }}
        """
    
    def _build_market_analysis_prompt(self, project_info: dict, with_search: bool = True) -> str:
        """构建市场分析提示词"""
        search_instruction = """
        **请搜索以下相关信息进行分析**:
        1. 该项目所在技术领域的最新市场趋势和发展状况
        2. 主要竞争对手和类似产品的市场表现
        3. 目标用户群体的市场规模和需求变化
        4. 相关行业的投资热度和商业模式发展
        5. 技术发展趋势和政策环境影响
        """ if with_search else ""
        
        task_desc = "深度市场分析（使用最新网络搜索信息）" if with_search else "深度市场分析"
        
        return f"""
        **任务：对优质项目进行{task_desc}**

        **角色**：你是一位资深的市场研究分析师和产业投资专家，拥有丰富的行业洞察力和市场嗅觉。{'基于最新的网络搜索信息，' if with_search else '基于你的专业知识和行业经验，'}对一个已经通过技术和产品层面评估的优质项目，进行全面的市场环境分析。

        **核心理念**：再好的产品，如果没有合适的市场时机和竞争环境，也可能失败。请{'使用网络搜索获取最新的市场信息，' if with_search else '基于你的专业知识'}评估这个项目在当前市场环境中的真实机会。

        **项目基础信息**:
        - 项目名称: {project_info.get('repo_name', 'Unknown')}
        - 项目描述: {project_info.get('description', 'No description')}
        - 技术栈: {project_info.get('language', 'Unknown')}
        - 产品评估总结: {project_info.get('summary', 'No summary')}

        {search_instruction}

        **市场分析框架 (请对以下5个维度进行深入分析并打分)**:

        1. **市场时机 (Market Timing)** (1-10分):
           - 当前是否是这个领域/技术的最佳时机？
           - 是否踩准了行业发展的节拍？
           - 用户接受度和技术成熟度是否匹配？

        2. **竞争格局 (Competitive Landscape)** (1-10分):
           - 现有竞争对手的实力如何？是否已经被巨头垄断？
           - 是否存在明显的市场空白或竞争薄弱环节？
           - 新进入者的壁垒高低如何？

        3. **目标市场规模 (Total Addressable Market)** (1-10分):
           - 潜在用户群体的规模和支付能力如何？
           - 市场是否具备足够的增长潜力？
           - 是否能从小众市场扩展到主流市场？

        4. **商业模式可行性 (Business Model Viability)** (1-10分):
           - 变现路径是否清晰可行？
           - 用户获取成本与生命周期价值的比例是否健康？
           - 是否具备网络效应或规模经济优势？

        5. **行业发展趋势 (Industry Trends)** (1-10分):
           - 是否顺应了当前的技术潮流和社会趋势？
           - 未来3-5年的行业发展是否有利于该项目？
           - 是否可能受到政策法规或技术变革的负面影响？

        **输出格式 (必须是严格的JSON对象, 所有分析必须使用中文)**:
        {{
          "market_timing": {{
            "score": <float>,
            "analysis": "<详细的中文分析>"
          }},
          "competitive_landscape": {{
            "score": <float>,
            "analysis": "<详细的中文分析>"
          }},
          "market_size": {{
            "score": <float>,
            "analysis": "<详细的中文分析>"
          }},
          "business_model": {{
            "score": <float>,
            "analysis": "<详细的中文分析>"
          }},
          "industry_trends": {{
            "score": <float>,
            "analysis": "<详细的中文分析>"
          }},
          "overall_market_assessment": {{
            "final_score": <float, 对五个维度得分进行加权平均>,
            "market_recommendation": "<GO (强烈推荐) | PROCEED (谨慎推荐) | HOLD (观望) | PASS (放弃)>",
            "key_risks": ["<主要风险1>", "<主要风险2>", "<主要风险3>"],
            "key_opportunities": ["<主要机会1>", "<主要机会2>", "<主要机会3>"],
            "summary": "<综合市场评估的最终中文总结{'(注：本分析基于通用行业知识，未使用实时搜索数据)' if not with_search else ''}>"
          }}
        }}
        """
    
    async def _analyze_market_with_search(self, project_info: dict) -> dict:
        """使用搜索功能的市场分析"""
        prompt = self._build_market_analysis_prompt(project_info, with_search=True)
        raw_response = await self._generate_with_search(prompt, settings.gemini_model)
        
        result = self._extract_json_from_response(raw_response)
        return self._calculate_market_score(result)
    
    async def _analyze_market_without_search(self, project_info: dict) -> dict:
        """不使用搜索的市场分析"""
        prompt = self._build_market_analysis_prompt(project_info, with_search=False)
        raw_response = await self._generate(prompt, settings.gemini_model)
        
        result = self._extract_json_from_response(raw_response)
        return self._calculate_market_score(result)
    
    def _extract_json_from_response(self, raw_response: str) -> dict:
        """从AI响应中提取JSON"""
        start_index = raw_response.find('{')
        end_index = raw_response.rfind('}')
        
        if start_index != -1 and end_index != -1:
            json_text = raw_response[start_index:end_index+1]
            return json.loads(json_text)
        else:
            raise ValueError("响应中未找到有效的JSON对象")
    
    def _calculate_overall_score(self, result: dict) -> dict:
        """计算评估的综合分数"""
        s1 = result.get("user_need_insight", {}).get("score", 0)
        s2 = result.get("differentiated_advantage", {}).get("score", 0)
        s3 = result.get("viral_potential", {}).get("score", 0)
        
        final_score = round((s1 * 0.3 + s2 * 0.4 + s3 * 0.3), 1)
        
        if "overall_assessment" not in result:
            result["overall_assessment"] = {}
        result["overall_assessment"]["final_score"] = final_score
        
        return result
    
    def _calculate_market_score(self, result: dict) -> dict:
        """计算市场分析的综合分数"""
        scores = [
            result.get("market_timing", {}).get("score", 0),
            result.get("competitive_landscape", {}).get("score", 0),
            result.get("market_size", {}).get("score", 0),
            result.get("business_model", {}).get("score", 0),
            result.get("industry_trends", {}).get("score", 0)
        ]
        
        final_score = round(sum(scores) / len(scores), 1)
        
        if "overall_market_assessment" not in result:
            result["overall_market_assessment"] = {}
        result["overall_market_assessment"]["final_score"] = final_score
        
        # 添加total_score字段以保持向后兼容
        result["total_score"] = final_score
        
        return result


# 创建服务实例供其他模块使用
analysis_service = AnalysisService()