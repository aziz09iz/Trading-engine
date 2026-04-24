from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return database_url


async def run_migrations(
    database_url: str,
    migrations_dir: str | Path,
    retries: int = 10,
    retry_delay_seconds: float = 2.0,
) -> None:
    normalized_url = _normalize_database_url(database_url)
    migrations_path = Path(migrations_dir)
    sql_files = sorted(migrations_path.glob("*.sql"))
    if not sql_files:
        return

    last_error: Exception | None = None
    for _ in range(retries):
        try:
            conn = await asyncpg.connect(normalized_url)
            try:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        filename TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                applied_rows = await conn.fetch("SELECT filename FROM schema_migrations")
                applied = {row["filename"] for row in applied_rows}

                for sql_file in sql_files:
                    if sql_file.name in applied:
                        continue
                    sql = sql_file.read_text(encoding="utf-8")
                    async with conn.transaction():
                        await conn.execute(sql)
                        await conn.execute(
                            "INSERT INTO schema_migrations (filename) VALUES ($1)",
                            sql_file.name,
                        )
                return
            finally:
                await conn.close()
        except Exception as exc:  # pragma: no cover
            last_error = exc
            await asyncio.sleep(retry_delay_seconds)

    if last_error is not None:
        raise last_error
