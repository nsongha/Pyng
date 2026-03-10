"""Pyng — GPS Validator.

Geofence check, distance calculation, spoofing detection.
Sử dụng geopy.distance cho tính toán khoảng cách chính xác.
"""

from dataclasses import dataclass

from geopy.distance import geodesic


@dataclass
class GPSValidationResult:
    """Kết quả validate GPS location."""

    is_valid: bool
    distance_m: float  # khoảng cách tới văn phòng (mét)
    message: str
    accuracy_warning: bool = False  # GPS accuracy thấp
    spoofing_detected: bool = False  # nghi ngờ fake GPS


def validate_location(
    lat: float,
    lng: float,
    office_lat: float,
    office_lng: float,
    radius_m: int = 120,
    accuracy_m: float | None = None,
    max_accuracy_m: float = 50.0,
) -> GPSValidationResult:
    """Validate GPS location so với văn phòng.

    Args:
        lat: Vĩ độ user.
        lng: Kinh độ user.
        office_lat: Vĩ độ văn phòng.
        office_lng: Kinh độ văn phòng.
        radius_m: Bán kính geofence (mét), default 120m.
        accuracy_m: Độ chính xác GPS của user (mét), None = không biết.
        max_accuracy_m: Ngưỡng accuracy chấp nhận được (mét), default 50m.

    Returns:
        GPSValidationResult: Kết quả validate.
    """
    # Tính khoảng cách (mét)
    user_point = (lat, lng)
    office_point = (office_lat, office_lng)
    distance = geodesic(user_point, office_point).meters

    # Spoofing detection: accuracy = 0 rất đáng ngờ
    spoofing = False
    if accuracy_m is not None and accuracy_m == 0:
        spoofing = True

    # Accuracy warning
    accuracy_warning = False
    if accuracy_m is not None and accuracy_m > max_accuracy_m:
        accuracy_warning = True

    # Geofence check
    is_valid = distance <= radius_m and not spoofing

    # Build message
    if spoofing:
        message = "🚨 Phát hiện GPS giả mạo (accuracy = 0). Vui lòng tắt fake GPS."
    elif not is_valid:
        message = (
            f"❌ Vị trí không hợp lệ\n"
            f"Cách văn phòng: {distance:.0f}m (vượt quá giới hạn {radius_m}m)"
        )
    elif accuracy_warning:
        message = (
            f"✅ Vị trí hợp lệ (cách {distance:.0f}m)\n"
            f"⚠️ GPS không ổn định (accuracy: {accuracy_m:.0f}m)"
        )
    else:
        message = f"✅ Vị trí hợp lệ (cách {distance:.0f}m)"

    return GPSValidationResult(
        is_valid=is_valid,
        distance_m=round(distance, 1),
        message=message,
        accuracy_warning=accuracy_warning,
        spoofing_detected=spoofing,
    )


# TODO: Integrate vào GPS check-in handler để detect spoofing giữa 2 lần check-in
# Chưa được gọi từ handler nào — kế hoạch dùng khi có lịch sử check-in đủ.
def check_travel_speed(
    prev_lat: float,
    prev_lng: float,
    prev_time_iso: str,
    curr_lat: float,
    curr_lng: float,
    curr_time_iso: str,
    max_speed_kmh: float = 500.0,
) -> bool:
    """Phát hiện spoofing bằng travel speed.

    Nếu tốc độ di chuyển giữa 2 lần check-in > max_speed_kmh → spoofing.

    Args:
        prev_lat, prev_lng: Tọa độ lần check-in trước.
        prev_time_iso: Thời gian lần trước (ISO string).
        curr_lat, curr_lng: Tọa độ hiện tại.
        curr_time_iso: Thời gian hiện tại (ISO string).
        max_speed_kmh: Tốc độ tối đa hợp lý (km/h), default 500.

    Returns:
        bool: True nếu nghi ngờ spoofing.
    """
    from datetime import datetime

    distance_km = geodesic((prev_lat, prev_lng), (curr_lat, curr_lng)).km

    prev_time = datetime.fromisoformat(prev_time_iso)
    curr_time = datetime.fromisoformat(curr_time_iso)
    time_diff_hours = (curr_time - prev_time).total_seconds() / 3600

    if time_diff_hours <= 0:
        return True  # Cùng thời điểm nhưng khác vị trí = spoofing

    speed = distance_km / time_diff_hours
    return speed > max_speed_kmh
