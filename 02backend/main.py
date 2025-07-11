"""
应用启动入口
"""
import uvicorn
from src.main import create_app
from src.core.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    ) 