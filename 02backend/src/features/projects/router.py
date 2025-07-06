"""
项目功能的 API 端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ...core.database import get_session
from . import models, schemas, service


router = APIRouter()


@router.get("/", response_model=List[schemas.ProjectRead])
async def get_projects(
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    stage: Optional[models.AnalysisStage] = Query(None, description="筛选特定分析阶段的项目"),
):
    """
    获取项目列表，支持分页和按分析阶段筛选。
    """
    return service.get_projects(
        session=session, skip=skip, limit=limit, stage=stage
    )


@router.get("/{project_id}", response_model=schemas.ProjectReadDetails)
async def get_project(
    project_id: int,
    session: Session = Depends(get_session)
):
    """获取单个项目的详细信息"""
    project = session.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.get("/by-repo/{owner}/{repo}", response_model=schemas.ProjectReadDetails)
async def get_project_by_repo(
    owner: str,
    repo: str,
    session: Session = Depends(get_session)
):
    """通过仓库名称获取项目"""
    project = service.get_project_by_repo_name(session, f"{owner}/{repo}")
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.get("/stats/summary", response_model=schemas.ProjectStats)
async def get_stats_summary(
    session: Session = Depends(get_session)
):
    """获取项目统计摘要"""
    return service.get_project_stats(session) 