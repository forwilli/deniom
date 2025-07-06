"""
项目功能的 Pydantic 数据模型

用于 API 的数据校验、序列化和文档生成。
将 API 的数据契约与数据库的内部模型解耦。
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from .models import AnalysisStage


# 基础模型，包含所有模型共有的字段
class ProjectBase(BaseModel):
    repo_full_name: str
    repo_name: str
    owner: str
    description: Optional[str] = None
    stars: int
    language: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# 用于项目列表页的精简模型
class ProjectRead(ProjectBase):
    id: int
    current_stage: AnalysisStage
    is_promising: Optional[bool]
    synthesis_score: Optional[float] = None
    
    class Config:
        orm_mode = True


# 用于项目详情页的完整模型
class ProjectReadDetails(ProjectRead):
    screening_result: Optional[Dict[str, Any]] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    market_insight_result: Optional[Dict[str, Any]] = None
    synthesis_result: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True

# 用于项目统计的摘要模型
class StageDistribution(BaseModel):
    screening: int
    evaluation: int
    market_insight: int
    synthesis: int
    rejected: int

class ProjectStats(BaseModel):
    total_projects: int
    active_projects: int
    stage_distribution: StageDistribution 