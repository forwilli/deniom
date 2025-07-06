"""
项目功能的核心业务逻辑
注意：分析流程已迁移到服务层，这里只保留数据查询功能
"""
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
import asyncio
from datetime import datetime

from . import models, schemas
from ...core.database import get_session
from ...services import opportunity_service

# --- 数据查询逻辑 ---

def get_projects(
    session: Session,
    skip: int,
    limit: int,
    stage: Optional[models.AnalysisStage]
) -> List[models.Project]:
    """获取项目列表"""
    query = select(models.Project)
    if stage:
        query = query.where(models.Project.current_stage == stage)
    
    query = query.order_by(
        models.Project.synthesis_score.desc().nullslast(),
        models.Project.stars.desc()
    ).offset(skip).limit(limit)
    
    return session.exec(query).all()

def get_project_by_repo_name(session: Session, repo_full_name: str) -> Optional[models.Project]:
    """通过仓库全名获取项目"""
    query = select(models.Project).where(models.Project.repo_full_name == repo_full_name)
    return session.exec(query).first()

def get_project_stats(session: Session) -> schemas.ProjectStats:
    """获取项目统计数据"""
    stage_counts = {
        stage.value: session.query(models.Project).filter(
            models.Project.current_stage == stage
        ).count() for stage in models.AnalysisStage
    }
    
    total_projects = session.query(models.Project).count()
    active_projects = sum(count for stage, count in stage_counts.items() if stage != "rejected")
    
    return schemas.ProjectStats(
        total_projects=total_projects,
        active_projects=active_projects,
        stage_distribution=schemas.StageDistribution(**stage_counts)
    )

# --- 核心分析流程已迁移到服务层 ---
# 使用服务层的opportunity_service处理所有分析流程

class ProjectAnalysisService:
    """
    项目分析服务 - 已重构为服务层的简单包装器
    保留此类以保持向后兼容性
    """
    def __init__(self):
        # 直接使用服务层的opportunity_service
        self._opportunity_service = opportunity_service

    async def run_screening_stage(self, target_date: datetime, max_projects: int, fetch_new: bool = True, concurrency: int = 10):
        """委托给服务层的opportunity_service"""
        return await self._opportunity_service.run_screening_stage(
            target_date=target_date,
            max_projects=max_projects,
            fetch_new=fetch_new,
            concurrency=concurrency
        )


    async def run_core_idea_filter_stage(self, max_projects: int, concurrency: int = 10):
        """委托给服务层的opportunity_service"""
        return await self._opportunity_service.run_core_idea_filter_stage(
            max_projects=max_projects,
            concurrency=concurrency
        )


    async def run_evaluation_stage(self, max_projects: int, concurrency: int = 5):
        """委托给服务层的opportunity_service"""
        return await self._opportunity_service.run_evaluation_stage(
            max_projects=max_projects,
            concurrency=concurrency
        )


    async def run_market_analysis_stage(self, max_projects: int = 5, concurrency: int = 3):
        """委托给服务层的opportunity_service"""
        return await self._opportunity_service.run_market_analysis_stage(
            max_projects=max_projects,
            concurrency=concurrency
        )


    async def run_full_pipeline(self, min_stars: int = 0):
        """委托给服务层实现"""
        print("请使用opportunity_service的方法运行完整分析流程")

# 创建一个服务实例供 router 和 cli 使用
project_service = ProjectAnalysisService() 