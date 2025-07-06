"""
想法验证服务编排器
处理用户想法验证请求
"""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from .analysis_service import analysis_service
from .market_service import market_service


class IdeaValidationService:
    """想法验证服务 - 对用户提交的创业想法进行专业分析"""
    
    def __init__(self):
        self.analysis_service = analysis_service
        self.market_service = market_service
    
    async def validate_idea(
        self, 
        idea_description: str,
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证用户提交的创业想法
        
        Args:
            idea_description: 想法描述
            user_context: 额外的用户背景信息
            
        Returns:
            包含验证结果的字典
        """
        validation_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        print(f"开始验证想法 ID: {validation_id}")
        
        # 准备想法数据
        idea_data = {
            "repo_name": "User Idea",  # 虚拟项目名
            "description": idea_description,
            "language": "Unknown",
            "context": user_context
        }
        
        # 执行四阶段分析
        results = {
            "validation_id": validation_id,
            "submitted_at": start_time.isoformat(),
            "idea_description": idea_description,
            "stages": {}
        }
        
        try:
            # 阶段1: 初步筛选
            print("执行阶段1: 初步筛选...")
            screening_result = await self._run_screening_stage(idea_data)
            results["stages"]["screening"] = screening_result
            
            if not screening_result.get("is_promising", False):
                results["final_verdict"] = "REJECTED"
                results["summary"] = f"想法未通过初步筛选: {screening_result.get('reason', '')}"
                return results
            
            # 阶段2: 核心想法评估
            print("执行阶段2: 核心想法评估...")
            core_idea_result = await self._run_core_idea_stage(idea_data)
            results["stages"]["core_idea"] = core_idea_result
            
            pass_count = sum([
                core_idea_result.get("is_painkiller", False),
                core_idea_result.get("is_novel", False),
                core_idea_result.get("has_viral_potential", False),
                core_idea_result.get("is_simple_and_elegant", False)
            ])
            
            if pass_count < 2:
                results["final_verdict"] = "REJECTED"
                results["summary"] = f"核心想法评估未达标 ({pass_count}/4)"
                return results
            
            # 阶段3: 深度产品评估
            print("执行阶段3: 深度产品评估...")
            product_result = await self._run_product_evaluation_stage(idea_data)
            results["stages"]["product_evaluation"] = product_result
            
            if product_result.get("overall_assessment", {}).get("recommendation") == "REJECT":
                results["final_verdict"] = "REJECTED"
                results["summary"] = "产品评估未通过"
                return results
            
            # 阶段4: 市场分析
            print("执行阶段4: 市场分析...")
            market_result = await self._run_market_analysis_stage(idea_data)
            results["stages"]["market_analysis"] = market_result
            
            # 综合评判
            results["final_verdict"] = self._determine_final_verdict(
                product_result, 
                market_result
            )
            results["summary"] = self._generate_summary(results)
            
            # 生成实施建议
            if results["final_verdict"] in ["HIGHLY_RECOMMENDED", "RECOMMENDED"]:
                results["implementation_suggestions"] = await self._generate_implementation_plan(
                    idea_data, 
                    results
                )
            
        except Exception as e:
            results["error"] = str(e)
            results["final_verdict"] = "ERROR"
            results["summary"] = f"验证过程出错: {e}"
        
        # 计算总耗时
        end_time = datetime.now()
        results["processing_time_seconds"] = (end_time - start_time).total_seconds()
        
        return results
    
    async def _run_screening_stage(self, idea_data: dict) -> dict:
        """运行初步筛选阶段"""
        return await self.analysis_service.perform_screening_analysis(idea_data)
    
    async def _run_core_idea_stage(self, idea_data: dict) -> dict:
        """运行核心想法评估阶段"""
        return await self.analysis_service.analyze_core_idea(idea_data)
    
    async def _run_product_evaluation_stage(self, idea_data: dict) -> dict:
        """运行产品深度评估阶段"""
        # 为用户想法构建虚拟README
        virtual_readme = self._build_virtual_readme(idea_data)
        
        return await self.analysis_service.analyze_project_readme(
            "User Submitted Idea",
            virtual_readme
        )
    
    async def _run_market_analysis_stage(self, idea_data: dict) -> dict:
        """运行市场分析阶段"""
        # 准备市场分析数据
        project_info = {
            "repo_name": "User Idea",
            "description": idea_data["description"],
            "language": "N/A",
            "stars": 0,
            "summary": idea_data.get("context", "用户提交的创业想法")
        }
        
        return await self.analysis_service.analyze_market(project_info)
    
    def _build_virtual_readme(self, idea_data: dict) -> str:
        """为用户想法构建虚拟README"""
        context = idea_data.get("context", "")
        
        return f"""
# {idea_data.get('repo_name', 'User Idea')}

## 项目概述

{idea_data['description']}

## 背景与动机

{context if context else '这是一个用户提交的创业想法，正在进行专业评估。'}

## 核心功能

基于描述，该想法的核心功能包括：
- 待AI分析后确定

## 目标用户

- 待AI分析后确定

## 技术方案

- 待确定

---
*注：这是一个虚拟的README，用于AI评估用户提交的想法。*
        """
    
    def _determine_final_verdict(
        self, 
        product_result: dict, 
        market_result: dict
    ) -> str:
        """综合判定最终结果"""
        product_score = product_result.get("overall_assessment", {}).get("final_score", 0)
        market_score = market_result.get("total_score", 0)
        
        avg_score = (product_score + market_score) / 2
        
        if avg_score >= 8.5:
            return "HIGHLY_RECOMMENDED"
        elif avg_score >= 7.0:
            return "RECOMMENDED"
        elif avg_score >= 5.5:
            return "WORTH_CONSIDERING"
        else:
            return "NOT_RECOMMENDED"
    
    def _generate_summary(self, results: dict) -> str:
        """生成验证总结"""
        verdict = results["final_verdict"]
        stages = results["stages"]
        
        if verdict == "REJECTED":
            return results.get("summary", "想法未通过验证")
        
        product_score = stages.get("product_evaluation", {}).get("overall_assessment", {}).get("final_score", 0)
        market_score = stages.get("market_analysis", {}).get("total_score", 0)
        
        verdict_text = {
            "HIGHLY_RECOMMENDED": "强烈推荐",
            "RECOMMENDED": "推荐",
            "WORTH_CONSIDERING": "值得考虑",
            "NOT_RECOMMENDED": "不推荐"
        }.get(verdict, verdict)
        
        return f"""
验证结果: {verdict_text}

产品评分: {product_score}/10
市场评分: {market_score}/10

核心优势:
- {stages.get('product_evaluation', {}).get('overall_assessment', {}).get('summary', 'N/A')}

市场机会:
- {stages.get('market_analysis', {}).get('overall_market_assessment', {}).get('summary', 'N/A')}
        """
    
    async def _generate_implementation_plan(
        self, 
        idea_data: dict, 
        validation_results: dict
    ) -> dict:
        """生成实施建议"""
        # 这里可以调用AI生成具体的实施计划
        # 目前返回基础框架
        return {
            "mvp_features": [
                "核心功能1",
                "核心功能2",
                "核心功能3"
            ],
            "tech_stack_recommendations": [
                "推荐技术栈1",
                "推荐技术栈2"
            ],
            "go_to_market_strategy": [
                "市场策略1",
                "市场策略2"
            ],
            "risk_mitigation": [
                "风险缓解措施1",
                "风险缓解措施2"
            ],
            "next_steps": [
                "1. 验证核心假设",
                "2. 构建MVP原型",
                "3. 寻找种子用户",
                "4. 迭代优化"
            ]
        }


# 创建服务实例供其他模块使用
idea_validation_service = IdeaValidationService()