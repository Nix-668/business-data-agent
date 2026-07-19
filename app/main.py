import os
import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from .database import initialize_database, schema_description
from .query_service import execute_readonly_query


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(value: str | None = Security(API_KEY_HEADER)) -> None:
    expected = os.getenv("DATA_AGENT_API_KEY", "change-me-before-deploying")
    if not value or value != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


class QueryRequest(BaseModel):
    sql: str = Field(description="只读 SELECT SQL，不允许修改数据库", max_length=5000)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Business Data Agent Tool API",
    version="0.1.0",
    description="供 Dify Agent 调用的只读经营数据查询工具。",
    lifespan=lifespan,
)


@app.get("/health", summary="检查服务状态")
def health() -> dict:
    return {"status": "ok"}


@app.get("/schema", summary="获取数据库表结构", dependencies=[Depends(verify_api_key)])
def get_schema() -> dict:
    return schema_description()


@app.post("/query", summary="执行只读 SQL", dependencies=[Depends(verify_api_key)])
def run_query(request: QueryRequest) -> dict:
    try:
        return execute_readonly_query(request.sql)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(status_code=400, detail=f"SQL 执行失败: {exc}") from exc
