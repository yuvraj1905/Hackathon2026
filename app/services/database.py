import os
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg


class DatabaseManager:
    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None

    def _get_database_url(self) -> str:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL not found in environment")
        return url

    def _normalize_for_asyncpg(self, database_url: str) -> str:
        """
        asyncpg does not accept all libpq query params.
        Keep the URL intact except unsupported params like channel_binding.
        """
        parsed = urlsplit(database_url)
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_params = [(k, v) for k, v in query_params if k != "channel_binding"]
        normalized_query = urlencode(filtered_params)
        return urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, normalized_query, parsed.fragment)
        )

    async def connect(self) -> None:
        if self.pool is not None:
            return

        database_url = self._normalize_for_asyncpg(self._get_database_url())
        self.pool = await asyncpg.create_pool(
            dsn=database_url,
            min_size=1,
            max_size=5,
            command_timeout=30,
        )

        # Ensure email pipeline table exists
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS email_estimate_requests (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    message_id TEXT UNIQUE,
                    sender_email TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    raw_body TEXT NOT NULL DEFAULT '',
                    attachments_count INT NOT NULL DEFAULT 0,
                    parsed_requirements JSONB,
                    estimate_result JSONB,
                    pdf_generated BOOLEAN NOT NULL DEFAULT FALSE,
                    reply_sent BOOLEAN NOT NULL DEFAULT FALSE,
                    sales_notified BOOLEAN NOT NULL DEFAULT FALSE,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)

    async def disconnect(self) -> None:
        if self.pool is None:
            return
        await self.pool.close()
        self.pool = None

    async def healthcheck(self) -> bool:
        if self.pool is None:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


db = DatabaseManager()
