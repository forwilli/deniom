"""
智能情报服务编排器
管理自动化分析流程，负责协调四阶段分析流程
"""
from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime
import asyncio

from ..core.database import get_session
from ..features.projects import models
from .github_service import github_service
from .analysis_service import analysis_service


class OpportunityService:
    """智能情报服务 - 管理自动化的项目发现和分析流程"""
    
    def __init__(self):
        self.github_service = github_service
        self.analysis_service = analysis_service
    
    async def run_screening_stage(
        self, 
        target_date: datetime, 
        max_projects: int, 
        fetch_new: bool = True, 
        concurrency: int = 10
    ) -> dict:
        """
        运行第一阶段：宽基筛选
        1. 从GitHub获取新项目
        2. 进行快速筛选
        """
        results = {
            "fetched": 0, 
            "newly_added": 0, 
            "screened": 0, 
            "passed": 0, 
            "rejected": 0, 
            "deleted": 0
        }
        
        with Session(next(get_session()).bind) as session:
            # 1. 清理旧的未分析项目
            if fetch_new:
                await self._clean_unanalyzed_projects(session, target_date, results)
            
            # 2. 从GitHub获取新项目
            if fetch_new:
                await self._fetch_new_projects(session, target_date, max_projects, results)
            
            # 3. 执行筛选
            await self._screen_projects(session, target_date, max_projects, concurrency, results)
            
        return results
    
    async def run_core_idea_filter_stage(
        self, 
        max_projects: int, 
        concurrency: int = 10
    ) -> dict:
        """运行第二阶段：核心想法筛选"""
        results = {"processed": 0, "passed": 0, "rejected": 0}
        
        with Session(next(get_session()).bind) as session:
            projects = await self._get_projects_by_stage(
                session, 
                models.AnalysisStage.CORE_IDEA_FILTERING, 
                max_projects
            )
            
            if not projects:
                print("没有找到需要进行核心想法筛选的项目。")
                return results
            
            results["processed"] = len(projects)
            await self._process_projects_concurrently(
                projects, 
                self._filter_one_project_by_core_idea, 
                session, 
                concurrency, 
                results
            )
            
        return results
    
    async def run_evaluation_stage(
        self, 
        max_projects: int, 
        concurrency: int = 5
    ) -> dict:
        """运行第三阶段：深度评估"""
        results = {"processed": 0, "success": 0, "no_readme": 0, "failed": 0}
        
        with Session(next(get_session()).bind) as session:
            projects = await self._get_projects_by_stage(
                session, 
                models.AnalysisStage.EVALUATION, 
                max_projects
            )
            
            if not projects:
                print("没有找到需要进行深度评估的项目。")
                return results
            
            results["processed"] = len(projects)
            
            semaphore = asyncio.Semaphore(concurrency)
            tasks = [
                self._evaluate_one_project(project, semaphore, session) 
                for project in projects
            ]
            eval_results = await asyncio.gather(*tasks)
            
            for status in eval_results:
                results[status] += 1
            
            session.commit()
            print("深度评估完成，数据库已更新。")
            
        return results
    
    async def run_market_analysis_stage(
        self, 
        max_projects: int = 5, 
        concurrency: int = 3
    ) -> dict:
        """运行第四阶段：市场分析"""
        results = {"processed": 0, "success": 0, "failed": 0}
        
        with Session(next(get_session()).bind) as session:
            projects = await self._get_top_projects_for_market_analysis(session, max_projects)
            
            if not projects:
                print("没有找到需要进行市场分析的项目。")
                return results
            
            results["processed"] = len(projects)
            self._display_projects_for_analysis(projects)
            
            semaphore = asyncio.Semaphore(concurrency)
            tasks = [
                self._analyze_one_project_market(project, semaphore, session) 
                for project in projects
            ]
            analysis_results = await asyncio.gather(*tasks)
            
            for status in analysis_results:
                results[status] += 1
            
            session.commit()
            print("市场分析完成，数据库已更新。")
            
        return results
    
    # --- 私有辅助方法 ---
    
    async def _clean_unanalyzed_projects(
        self, 
        session: Session, 
        target_date: datetime, 
        results: dict
    ):
        """清理未分析的项目"""
        projects_to_delete = session.exec(
            select(models.Project).where(
                models.Project.batch_date == target_date,
                models.Project.current_stage == models.AnalysisStage.SCREENING
            )
        ).all()
        
        results["deleted"] = len(projects_to_delete)
        
        if projects_to_delete:
            for project in projects_to_delete:
                session.delete(project)
            session.commit()
            print(f"已清理 {results['deleted']} 个未分析的项目记录。")
    
    async def _fetch_new_projects(
        self, 
        session: Session, 
        target_date: datetime, 
        max_projects: int, 
        results: dict
    ):
        """从GitHub获取新项目"""
        print(f"正在从 GitHub 获取 {target_date.strftime('%Y-%m-%d')} 的新项目...")
        raw_projects = await self.github_service.search_newly_created_repos(
            target_date=target_date, 
            limit=max_projects
        )
        results["fetched"] = len(raw_projects)
        
        new_count = 0
        for raw_project in raw_projects:
            if not self._project_exists(session, target_date, raw_project['full_name']):
                self._add_new_project(session, target_date, raw_project)
                new_count += 1
        
        if new_count > 0:
            session.commit()
            print(f"新增 {new_count} 个项目到数据库。")
        results["newly_added"] = new_count
    
    async def _screen_projects(
        self, 
        session: Session, 
        target_date: datetime, 
        max_projects: int, 
        concurrency: int, 
        results: dict
    ):
        """执行项目筛选"""
        projects = session.exec(
            select(models.Project).where(
                models.Project.current_stage == models.AnalysisStage.SCREENING,
                models.Project.batch_date == target_date
            ).limit(max_projects)
        ).all()
        
        if not projects:
            print("没有找到需要筛选的项目。")
            return
        
        results["screened"] = len(projects)
        print(f"找到 {len(projects)} 个项目进行统一筛选...")
        
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [
            self._screen_one_project(project, semaphore, session) 
            for project in projects
        ]
        screening_results = await asyncio.gather(*tasks)
        
        for passed in screening_results:
            if passed:
                results["passed"] += 1
            else:
                results["rejected"] += 1
        
        session.commit()
        print("统一筛选完成，数据库已更新。")
    
    async def _screen_one_project(
        self, 
        project: models.Project, 
        semaphore: asyncio.Semaphore, 
        session: Session
    ) -> bool:
        """筛选单个项目"""
        async with semaphore:
            print(f"  正在筛选: {project.repo_full_name}...")
            
            project_data = {
                "repo_name": project.repo_full_name,
                "description": project.description,
                "stars": project.stars,
                "language": project.language
            }
            
            ai_result = await self.analysis_service.perform_screening_analysis(project_data)
            
            project.screening_result = ai_result
            is_promising = ai_result.get("is_promising", False)
            project.is_promising = is_promising
            
            if is_promising:
                project.current_stage = models.AnalysisStage.CORE_IDEA_FILTERING
                print(f"    -> [PASS-1] {project.repo_full_name}")
                return True
            else:
                project.current_stage = models.AnalysisStage.REJECTED
                print(f"    -> [REJECT-1] {project.repo_full_name} (Reason: {ai_result.get('reason')})")
                return False
    
    async def _filter_one_project_by_core_idea(
        self, 
        project: models.Project, 
        semaphore: asyncio.Semaphore, 
        session: Session
    ) -> bool:
        """核心想法筛选单个项目"""
        async with semaphore:
            print(f"  核心想法筛选: {project.repo_full_name}...")
            
            project_data = {
                "repo_name": project.repo_full_name,
                "description": project.description
            }
            
            ai_result = await self.analysis_service.analyze_core_idea(project_data)
            project.core_idea_result = ai_result
            
            # 应用"4个中满足2个"的规则
            pass_count = sum([
                ai_result.get("is_painkiller", False),
                ai_result.get("is_novel", False),
                ai_result.get("has_viral_potential", False),
                ai_result.get("is_simple_and_elegant", False)
            ])
            
            if pass_count >= 2:
                project.current_stage = models.AnalysisStage.EVALUATION
                print(f"    -> [PASS-2] {project.repo_full_name} (Met {pass_count}/4 criteria)")
                return True
            else:
                project.current_stage = models.AnalysisStage.REJECTED
                print(f"    -> [REJECT-2] {project.repo_full_name} (Met {pass_count}/4 criteria)")
                return False
    
    async def _evaluate_one_project(
        self, 
        project: models.Project, 
        semaphore: asyncio.Semaphore, 
        session: Session
    ) -> str:
        """深度评估单个项目"""
        async with semaphore:
            print(f"  正在深度评估: {project.repo_full_name}...")
            
            # 获取README
            readme_content = await self.github_service.get_readme_content(
                project.owner, 
                project.repo_name
            )
            
            if not readme_content:
                print(f"    -> [REJECT-3] 无法获取 {project.repo_full_name} 的 README")
                project.current_stage = models.AnalysisStage.REJECTED
                project.evaluation_result = {"error": "Failed to fetch README."}
                return "no_readme"
            
            # AI分析
            ai_result = await self.analysis_service.analyze_project_readme(
                project.repo_full_name, 
                readme_content
            )
            
            project.evaluation_result = ai_result
            
            # 根据推荐结果更新状态
            if self._is_project_passed_evaluation(ai_result):
                project.current_stage = models.AnalysisStage.MARKET_INSIGHT
                recommendation = ai_result['overall_assessment'].get('recommendation', '')
                final_score = ai_result['overall_assessment'].get('final_score', 0)
                print(f"    -> [PASS-3] {project.repo_full_name} ({recommendation}, {final_score}分)")
                return "success"
            else:
                project.current_stage = models.AnalysisStage.REJECTED
                print(f"    -> [REJECT-3] {project.repo_full_name}")
                return "failed"
    
    async def _analyze_one_project_market(
        self, 
        project: models.Project, 
        semaphore: asyncio.Semaphore, 
        session: Session
    ) -> str:
        """市场分析单个项目"""
        async with semaphore:
            print(f"  正在进行市场分析: {project.repo_full_name}...")
            
            try:
                project_info = {
                    "repo_name": project.repo_full_name,
                    "description": project.description,
                    "language": project.language,
                    "stars": project.stars,
                    "summary": self._get_project_summary(project)
                }
                
                market_result = await self.analysis_service.analyze_market(project_info)
                project.market_insight_result = market_result
                
                if self._is_market_analysis_passed(market_result):
                    project.current_stage = models.AnalysisStage.SYNTHESIS
                    market_score = market_result.get('total_score', 0)
                    print(f"    -> [PASS-4] {project.repo_full_name} (市场分: {market_score})")
                    return "success"
                else:
                    project.current_stage = models.AnalysisStage.REJECTED
                    print(f"    -> [REJECT-4] {project.repo_full_name}")
                    return "failed"
                    
            except Exception as e:
                print(f"    -> [ERROR] {project.repo_full_name} 市场分析失败: {e}")
                project.current_stage = models.AnalysisStage.REJECTED
                project.market_insight_result = {"error": str(e)}
                return "failed"
    
    # --- 辅助方法 ---
    
    async def _get_projects_by_stage(
        self, 
        session: Session, 
        stage: models.AnalysisStage, 
        limit: int
    ) -> List[models.Project]:
        """获取指定阶段的项目"""
        return session.exec(
            select(models.Project).where(
                models.Project.current_stage == stage
            ).limit(limit)
        ).all()
    
    async def _get_top_projects_for_market_analysis(
        self, 
        session: Session, 
        limit: int
    ) -> List[models.Project]:
        """获取评分最高的项目进行市场分析"""
        all_projects = session.exec(
            select(models.Project).where(
                models.Project.current_stage == models.AnalysisStage.MARKET_INSIGHT
            )
        ).all()
        
        # 按评分排序
        def get_final_score(project):
            if not project.evaluation_result or not isinstance(project.evaluation_result, dict):
                return 0
            return project.evaluation_result.get('overall_assessment', {}).get('final_score', 0)
        
        return sorted(all_projects, key=get_final_score, reverse=True)[:limit]
    
    async def _process_projects_concurrently(
        self, 
        projects: List[models.Project],
        process_func, 
        session: Session, 
        concurrency: int, 
        results: dict
    ):
        """并发处理项目"""
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [process_func(project, semaphore, session) for project in projects]
        process_results = await asyncio.gather(*tasks)
        
        for passed in process_results:
            if passed:
                results["passed"] += 1
            else:
                results["rejected"] += 1
        
        session.commit()
    
    def _project_exists(
        self, 
        session: Session, 
        batch_date: datetime, 
        repo_full_name: str
    ) -> bool:
        """检查项目是否已存在"""
        return session.exec(
            select(models.Project).where(
                models.Project.batch_date == batch_date,
                models.Project.repo_full_name == repo_full_name
            )
        ).first() is not None
    
    def _add_new_project(
        self, 
        session: Session, 
        batch_date: datetime, 
        raw_project: dict
    ):
        """添加新项目到数据库"""
        owner, repo_name = raw_project['full_name'].split('/')
        new_project = models.Project(
            batch_date=batch_date,
            repo_full_name=raw_project['full_name'],
            owner=owner,
            repo_name=repo_name,
            description=raw_project.get('description'),
            stars=raw_project.get('stargazers_count', 0),
            language=raw_project.get('language'),
            created_at=datetime.fromisoformat(raw_project['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(raw_project['updated_at'].replace('Z', '+00:00')),
        )
        session.add(new_project)
    
    def _is_project_passed_evaluation(self, ai_result: dict) -> bool:
        """判断项目是否通过评估"""
        if not isinstance(ai_result, dict) or 'overall_assessment' not in ai_result:
            return False
        
        recommendation = ai_result['overall_assessment'].get('recommendation', '')
        passed_recommendations = ['DIAMOND', 'HIDDEN GEM', 'SOLID BET']
        
        return any(rec in recommendation for rec in passed_recommendations)
    
    def _is_market_analysis_passed(self, market_result: dict) -> bool:
        """判断市场分析是否通过"""
        if not isinstance(market_result, dict) or 'total_score' not in market_result:
            return False
        
        return market_result.get('total_score', 0) >= 7.0
    
    def _get_project_summary(self, project: models.Project) -> str:
        """获取项目评估总结"""
        if not project.evaluation_result or not isinstance(project.evaluation_result, dict):
            return "未找到产品评估信息"
        
        return project.evaluation_result.get('overall_assessment', {}).get('summary', '未找到评估总结')
    
    def _display_projects_for_analysis(self, projects: List[models.Project]):
        """显示即将分析的项目"""
        print("\n=== 即将进行市场分析的项目 ===")
        for i, project in enumerate(projects, 1):
            eval_score = "N/A"
            if project.evaluation_result and isinstance(project.evaluation_result, dict):
                eval_score = project.evaluation_result.get('overall_assessment', {}).get('final_score', 'N/A')
            print(f"  {i:2d}. {project.repo_full_name} (评估分: {eval_score})")
        print("=" * 50)


# 创建服务实例供其他模块使用
opportunity_service = OpportunityService()