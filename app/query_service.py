import re
import sqlite3

from .database import connect


MAX_ROWS = 200
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)


def validate_sql(raw_sql: str) -> str:
    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()
    if not sql:
        raise ValueError("SQL 不能为空")
    if ";" in sql:
        raise ValueError("只允许执行一条 SQL")
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise ValueError("SQL 中不允许注释")
    if not re.match(r"^(select|with)\b", sql, re.IGNORECASE):
        raise ValueError("只允许 SELECT 或只读 WITH 查询")
    if FORBIDDEN.search(sql):
        raise ValueError("检测到禁止的数据库操作")
    return sql


def execute_readonly_query(raw_sql: str) -> dict:
    sql = validate_sql(raw_sql)
    conn = connect(read_only=True)
    try:
        cursor = conn.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        rows = cursor.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]
        return {
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
            "executed_sql": sql,
        }
    finally:
        conn.close()

