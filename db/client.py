"""Pyng — Supabase DB client module.

Singleton pattern: lazy init, tránh tạo lại connection mỗi request.
Dùng service_role_key để bypass RLS (server-side operations).
"""

from supabase import create_client, Client

from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# Singleton instance
_client: Client | None = None


def get_client() -> Client:
    """Lấy Supabase client (singleton).

    Returns:
        Client: Supabase client instance.

    Raises:
        ValueError: Nếu SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY chưa cấu hình.
    """
    global _client

    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    return _client
