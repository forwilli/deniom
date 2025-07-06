"""
数据库配置模块

使用 SQLModel 作为 ORM，SQLite 作为数据库。
"""

from sqlmodel import create_engine, SQLModel, Session
from .config import settings


# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    echo=settings.debug  # 在调试模式下打印 SQL 语句
)


def init_db():
    """初始化数据库，创建所有表"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session 