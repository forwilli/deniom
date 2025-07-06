import pytest
from httpx import AsyncClient
from fastapi import status

# 将项目根目录添加到sys.path，以便pytest可以找到app模块
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app


@pytest.mark.asyncio
async def test_health_check():
    """
    测试 /health 端点
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root():
    """
    测试根路径 / 端点
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == status.HTTP_200_OK
    # 检查响应中是否包含预期的键
    data = response.json()
    assert "message" in data
    assert "version" in data 