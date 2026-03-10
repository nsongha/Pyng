"""Pyng — WiFi Validator.

Validate WiFi SSID against whitelist từ database.
"""

from dataclasses import dataclass


@dataclass
class WiFiValidationResult:
    """Kết quả validate WiFi SSID."""

    is_valid: bool
    message: str
    matched_ssid: str | None = None  # SSID matched (nếu valid)
    valid_ssids: list[str] | None = None  # Danh sách SSID hợp lệ (nếu invalid)


def validate_wifi(ssid: str, whitelist: list[dict]) -> WiFiValidationResult:
    """Validate WiFi SSID với whitelist.

    Args:
        ssid: Tên WiFi user nhập.
        whitelist: List of whitelist records từ DB, mỗi record có key 'ssid'.

    Returns:
        WiFiValidationResult: Kết quả validate.
    """
    if not ssid or not ssid.strip():
        return WiFiValidationResult(
            is_valid=False,
            message="❌ Vui lòng nhập tên WiFi.",
        )

    ssid_clean = ssid.strip()
    valid_ssids = [w["ssid"] for w in whitelist if w.get("is_active", True)]

    # Case-insensitive match
    for valid_ssid in valid_ssids:
        if ssid_clean.lower() == valid_ssid.lower():
            return WiFiValidationResult(
                is_valid=True,
                message=f"✅ WiFi \"{valid_ssid}\" hợp lệ",
                matched_ssid=valid_ssid,
            )

    # Không match
    ssid_list = "\n".join(f"• {s}" for s in valid_ssids) if valid_ssids else "Chưa cấu hình"
    return WiFiValidationResult(
        is_valid=False,
        message=(
            f"❌ WiFi \"{ssid_clean}\" không có trong danh sách văn phòng.\n\n"
            f"WiFi hợp lệ:\n{ssid_list}"
        ),
        valid_ssids=valid_ssids,
    )
