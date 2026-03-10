"""Pyng — Supabase REST client module.

Lightweight wrapper quanh Supabase PostgREST API, dùng httpx thay SDK.
Lý do: supabase SDK conflict httpx version với python-telegram-bot trên Vercel.

Singleton pattern: lazy init, tránh tạo lại connection mỗi request.
Dùng service_role_key để bypass RLS (server-side operations).
"""

import httpx

from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


# REST base URL
_REST_BASE: str = ""

# Shared headers
_HEADERS: dict[str, str] = {}


def _ensure_init() -> None:
    """Khởi tạo REST base URL và headers (lazy, 1 lần duy nhất)."""
    global _REST_BASE, _HEADERS

    if _REST_BASE:
        return

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env"
        )

    _REST_BASE = f"{SUPABASE_URL.rstrip('/')}/rest/v1"
    _HEADERS = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _build_filters(filters: dict) -> dict[str, str]:
    """Chuyển dict filters sang PostgREST query params.

    Hỗ trợ:
        {"col": value}           → col=eq.value
        {"col.gte": value}       → col=gte.value
        {"col.lt": value}        → col=lt.value
        {"col.neq": value}       → col=neq.value

    Args:
        filters: Dict filter conditions.

    Returns:
        dict: PostgREST-compatible query params.
    """
    params: dict[str, str] = {}
    for key, value in filters.items():
        if "." in key:
            col, op = key.rsplit(".", 1)
            params[col] = f"{op}.{value}"
        else:
            params[key] = f"eq.{value}"
    return params


def select(
    table: str,
    columns: str = "*",
    *,
    filters: dict | None = None,
    order: str | None = None,
    limit: int | None = None,
    count: bool = False,
) -> list[dict] | int:
    """SELECT rows từ table.

    Args:
        table: Tên table.
        columns: Columns cần select (default "*").
        filters: PostgREST filter dict.
        order: Order string, vd "checked_at.desc".
        limit: Giới hạn số rows.
        count: Nếu True, trả về count thay vì data.

    Returns:
        list[dict]: Rows data. Hoặc int nếu count=True.
    """
    _ensure_init()
    params: dict[str, str] = {"select": columns}

    if filters:
        params.update(_build_filters(filters))
    if order:
        params["order"] = order
    if limit:
        params["limit"] = str(limit)

    headers = {**_HEADERS}
    if count:
        headers["Prefer"] = "count=exact"
        headers["Range-Unit"] = "items"

    resp = httpx.get(f"{_REST_BASE}/{table}", headers=headers, params=params)
    resp.raise_for_status()

    if count:
        # PostgREST trả count trong Content-Range header: "0-0/5"
        content_range = resp.headers.get("content-range", "")
        if "/" in content_range:
            total = content_range.split("/")[-1]
            return int(total) if total != "*" else 0
        return 0

    return resp.json()


def insert(table: str, data: dict) -> dict:
    """INSERT 1 row vào table.

    Args:
        table: Tên table.
        data: Dict data insert.

    Returns:
        dict: Row vừa tạo.
    """
    _ensure_init()
    headers = {**_HEADERS, "Prefer": "return=representation"}

    resp = httpx.post(f"{_REST_BASE}/{table}", headers=headers, json=data)
    resp.raise_for_status()

    rows = resp.json()
    return rows[0] if rows else {}


def update(table: str, data: dict, *, filters: dict) -> dict | None:
    """UPDATE rows matching filters.

    Args:
        table: Tên table.
        data: Dict data update.
        filters: Filter conditions (bắt buộc để tránh update all).

    Returns:
        dict | None: Row vừa update, hoặc None nếu không match.
    """
    _ensure_init()
    headers = {**_HEADERS, "Prefer": "return=representation"}
    params = _build_filters(filters)

    resp = httpx.patch(f"{_REST_BASE}/{table}", headers=headers, json=data, params=params)
    resp.raise_for_status()

    rows = resp.json()
    return rows[0] if rows else None


def delete(table: str, *, filters: dict) -> list[dict]:
    """DELETE rows matching filters.

    Args:
        table: Tên table.
        filters: Filter conditions (bắt buộc để tránh delete all).

    Returns:
        list[dict]: Rows đã xóa.
    """
    _ensure_init()
    headers = {**_HEADERS, "Prefer": "return=representation"}
    params = _build_filters(filters)

    resp = httpx.delete(f"{_REST_BASE}/{table}", headers=headers, params=params)
    resp.raise_for_status()

    return resp.json()
