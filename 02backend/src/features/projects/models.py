"""
项目数据模型

定义 GitHub 项目的数据结构，对应四阶段分析流程中的数据。
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON, Column, UniqueConstraint
from enum import Enum


class AnalysisStage(str, Enum):
    """分析阶段枚举"""
    SCREENING = "screening"  # 筛选
    CORE_IDEA_FILTERING = "core_idea_filtering" # 核心想法筛选
    EVALUATION = "evaluation"  # 深度评估
    MARKET_INSIGHT = "market_insight"  # 市场洞察
    SYNTHESIS = "synthesis"  # 顶尖合成
    REJECTED = "rejected" # 不被看好


class Project(SQLModel, table=True):
    """GitHub 项目模型"""
    
    # 基础信息
    id: Optional[int] = Field(default=None, primary_key=True)
    batch_date: datetime = Field(index=True) # 数据批次日期
    repo_full_name: str = Field(index=True, unique=True)  # owner/repo 格式
    repo_name: str
    owner: str
    description: Optional[str] = None
    stars: int = 0
    language: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 分析状态
    current_stage: AnalysisStage = Field(default=AnalysisStage.SCREENING)
    is_active: bool = True  # 是否在当前分析周期中活跃
    is_promising: Optional[bool] = Field(default=None, index=True) # AI初筛是否有潜力
    
    # 分析结果 - 使用 JSON 字段存储复杂数据
    screening_result: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSON)
    )
    evaluation_result: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    core_idea_result: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    market_insight_result: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    synthesis_result: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    synthesis_score: Optional[float] = None  # 最终综合评分
    
    # 时间戳
    analyzed_at: Optional[datetime] = None
    created_at_db: datetime = Field(default_factory=datetime.utcnow)
    updated_at_db: datetime = Field(default_factory=datetime.utcnow)
    
    # 联合唯一约束，确保同一批次内不会有重复的仓库
    __table_args__ = (
        UniqueConstraint("batch_date", "repo_full_name", name="unique_batch_repo"),
    ) 