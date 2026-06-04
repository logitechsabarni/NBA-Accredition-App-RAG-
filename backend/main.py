"""
NBA Enterprise AI Platform — Application Entry Point
Run with: uvicorn main:app --host 0.0.0.0 --port 8000
"""

import uvicorn

from app import create_application
from config.settings import settings

app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=1 if settings.RELOAD else settings.WORKERS,
        loop="uvloop",
        http="httptools",
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
