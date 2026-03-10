"""Pyng — Shared timezone helper.

Singleton pattern: lazy init ZoneInfo từ TIMEZONE setting.
Dùng chung cho services và handlers thay vì duplicate pattern.
"""

import logging
from zoneinfo import ZoneInfo

from config.settings import TIMEZONE

logger = logging.getLogger(__name__)

# Singleton instance
_tz: ZoneInfo | None = None


def get_tz() -> ZoneInfo:
    """Lấy ZoneInfo instance (singleton).

    Returns:
        ZoneInfo: Timezone instance theo config.
    """
    global _tz
    if _tz is None:
        _tz = ZoneInfo(TIMEZONE)
    return _tz
