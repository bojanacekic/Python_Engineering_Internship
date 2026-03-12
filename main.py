"""
Application entrypoint for the Claude Code Telemetry Analytics Platform.

Run with: python main.py
Serves the FastAPI app with uvicorn (host 0.0.0.0, port 8000).
"""
import uvicorn

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
