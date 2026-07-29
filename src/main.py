from dotenv import load_dotenv

load_dotenv()

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from src.router import agent_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="langgraph-agent", version="0.1.0")
app.include_router(agent_router.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "online", "message": "langgraph-agent server is running"}


class NoCacheStaticFiles(StaticFiles):
    """정적 파일(HTML/CSS/JS)이 브라우저 캐시에 오래 남아
    수정 사항이 새로고침에도 반영 안 되는 걸 막기 위해 캐시를 비활성화."""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/", NoCacheStaticFiles(directory="static", html=True), name="static")
