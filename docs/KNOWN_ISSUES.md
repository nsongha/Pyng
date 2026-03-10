# KNOWN_ISSUES.md — Bugs & Edge Cases đã biết

> File này ghi lại các vấn đề đã biết, cách workaround, và trạng thái xử lý.  
> Cập nhật liên tục trong quá trình phát triển và vận hành.

---

## Format

```
### ISSUE-XXX: [Tên vấn đề]
**Severity**: Critical | High | Medium | Low
**Status**: Open | In Progress | Resolved | Won't Fix
**Affects**: GPS | WiFi | QR | NFC | Admin | Report | All
**Workaround**: Cách tạm thời
**Root Cause**: Nguyên nhân (nếu biết)
**Fix**: Kế hoạch sửa
```

---

## 🔴 Critical

### ISSUE-001: GPS giả mạo bằng mock location app

**Severity**: Critical  
**Status**: Partially Mitigated  
**Affects**: GPS

**Mô tả**: Android cho phép dùng app "Mock Location" để giả tọa độ GPS.

**Workaround hiện tại**:

- Kiểm tra tốc độ di chuyển bất thường (>500 km/h giữa 2 lần check-in)
- Kiểm tra GPS accuracy: nếu accuracy = 0m (quá hoàn hảo) → nghi ngờ
- Admin review log nếu thấy pattern bất thường

**Root Cause**: Giới hạn của Telegram API — không thể detect mock location từ phía server.

**Long-term fix**: Kết hợp với WiFi verification để double-check. Face++ verification ở Phase 2.

---

### ISSUE-002: Supabase free tier pause sau 1 tuần không active

**Severity**: Critical  
**Status**: Mitigated  
**Affects**: All

**Mô tả**: Supabase free tier tự pause project sau 7 ngày không có traffic.

**Workaround**: Cron job ping database mỗi 3 ngày:

```python
# scheduler.py
scheduler.add_job(
    ping_database,
    'interval',
    days=3,
    id='db_keepalive'
)
```

**Fix**: Upgrade Supabase lên Pro ($25/tháng) nếu budget cho phép.

---

## 🟠 High

### ISSUE-003: iOS NFC không hoạt động trên iPhone 6 trở xuống

**Severity**: High  
**Status**: Won't Fix  
**Affects**: NFC

**Mô tả**: iPhone 6 và cũ hơn không có NFC chip.

**Workaround**: Dùng QR code thay thế. Trong USAGE.md đã ghi rõ yêu cầu iPhone 7+.

---

### ISSUE-004: QR scan trên Telegram Desktop không hoạt động

**Severity**: High  
**Status**: Open  
**Affects**: QR

**Mô tả**: Telegram Desktop (PC/Mac) không có camera scan QR trực tiếp trong app.

**Workaround**:

- Dùng Telegram mobile để scan QR
- Hoặc dùng camera ngoài app (scan → copy link → paste vào Telegram)

**Fix kế hoạch**: Thêm option "Nhập mã QR thủ công" — nhân viên nhìn 6 ký tự trên màn hình và gõ vào.

---

### ISSUE-005: WiFi SSID giống nhau ở nhiều nơi

**Severity**: High  
**Status**: Open  
**Affects**: WiFi

**Mô tả**: SSID như "Vietnam Airlines WiFi" hay "Coffee WiFi" có thể trùng với WiFi văn phòng nếu đặt tên phổ biến.

**Root Cause**: WiFi check chỉ dựa vào SSID (tên), không verify MAC address router.

**Workaround**:

- Đặt tên WiFi công ty độc đáo (ví dụ: "Acme_Corp_5G_2026")
- Admin thêm mô tả rõ khi add SSID vào whitelist
- Xem xét kết hợp GPS + WiFi (cả hai phải pass) cho môi trường cần bảo mật cao

**Fix kế hoạch**: Mini App (Web NFC API) có thể đọc BSSID (MAC address) → verify chính xác hơn.

---

### ISSUE-006: Telegram rate limiting khi gửi nhiều notification cùng lúc

**Severity**: High  
**Status**: Mitigated  
**Affects**: Scheduler/Notifications

**Mô tả**: Telegram giới hạn 30 messages/second cho bot. Khi nhắc 50 người cùng lúc lúc 8:30 → có thể bị rate limit.

**Workaround**:

```python
# Gửi với delay nhỏ giữa các tin
for user in users:
    await bot.send_message(user.telegram_id, message)
    await asyncio.sleep(0.05)  # 50ms delay = tối đa 20 msg/s, dưới ngưỡng
```

**Status**: Đã implement delay, monitoring.

---

## 🟡 Medium

### ISSUE-007: Check-in lúc thay ca đêm (sau 23:00)

**Severity**: Medium  
**Status**: Open  
**Affects**: All

**Mô tả**: Auto check-out lúc 23:59 sẽ conflict nếu ai đó làm ca đêm và check-in sau 22:00.

**Workaround**: Admin có thể tắt auto-checkout cho user cụ thể.

**Fix kế hoạch**: Thêm config "shift type" (ca ngày / ca đêm) per user.

---

### ISSUE-008: Multiple check-in cùng ngày khi ra ngoài rồi vào lại

**Severity**: Medium  
**Status**: Open  
**Affects**: All

**Mô tả**: Nhân viên ra ngoài ăn trưa → check-out → vào lại → check-in → hệ thống tính 2 record, báo cáo lộn xộn.

**Workaround**: Bot nhắc "Bạn đã check-in hôm nay. Bạn có muốn check-out và vào lại không?"

**Fix kế hoạch**: Hỗ trợ multi-session trong ngày, tính tổng giờ = sum(session durations).

---

### ISSUE-009: GPS drift trong tòa nhà cao tầng

**Severity**: Medium  
**Status**: Won't Fix (limitation của GPS)  
**Affects**: GPS

**Mô tả**: Tòa nhà cao, nhiều kính có thể làm GPS drift xa hơn thực tế 50–200m.

**Workaround**:

- Tăng radius geofence lên 200m nếu văn phòng trong tòa nhà cao tầng
- Khuyến khích dùng WiFi là primary method cho văn phòng trong tòa nhà

---

### ISSUE-010: NFC tag bị nhiễu khi đặt gần kim loại

**Severity**: Medium  
**Status**: Documented  
**Affects**: NFC

**Mô tả**: Tag NFC đặt gần khung cửa kim loại có thể giảm read range.

**Workaround**:

- Dùng "anti-metal NFC tag" (có lớp ferrite backing)
- Dán cách khung kim loại ít nhất 2cm
- Hoặc dán lên vật liệu nhựa/gỗ

---

### ISSUE-011: Bot không nhận file ảnh lớn khi manual check-in

**Severity**: Medium  
**Status**: Open  
**Affects**: Manual Fallback

**Mô tả**: Telegram giới hạn 20MB cho file qua bot. Camera hiện đại chụp RAW có thể vượt qưỡng.

**Workaround**: Bot thông báo "Ảnh quá lớn, hãy dùng camera thường (không phải pro mode)".

**Fix kế hoạch**: Compress ảnh phía client trước khi gửi (nếu dùng Mini App).

---

## 🟢 Low

### ISSUE-012: Leaderboard không update real-time

**Severity**: Low  
**Status**: By Design  
**Affects**: Gamification

**Mô tả**: Leaderboard cập nhật mỗi giờ, không phải real-time.

**Note**: Đây là thiết kế có chủ đích để giảm tải DB query. Chấp nhận.

---

### ISSUE-013: Emoji không hiển thị đúng trên một số thiết bị Android cũ

**Severity**: Low  
**Status**: Won't Fix  
**Affects**: UI/UX

**Mô tả**: Android 7 trở xuống có thể không render được một số emoji mới (🏷️, 🦾...).

**Workaround**: Chấp nhận. Target user đã có thiết bị đủ mới.

---

### ISSUE-014: Timezone mismatch nếu nhân viên đang ở nước ngoài

**Severity**: Low  
**Status**: Open  
**Affects**: Scheduler, Report

**Mô tả**: Bot dùng timezone cố định (Asia/HCM). Nhân viên đang công tác ở nước khác nhận nhắc check-in lúc 3am giờ địa phương.

**Workaround**: Nhân viên tự tắt notification tạm thời khi đi công tác.

**Fix kế hoạch**: Thêm "vacation mode" — admin đánh dấu user đang công tác nước ngoài, tắt auto-remind.

---

## ✅ Resolved

### ISSUE-015: Supabase Python SDK conflict httpx version → Vercel build fail

**Severity**: Critical  
**Status**: ✅ Resolved (2026-03-10)  
**Affects**: Deploy

**Mô tả**: `supabase==2.3.0` yêu cầu `httpx==0.24.1`, conflict với `python-telegram-bot==21.5` (cần `httpx~=0.27`). Vercel build fail ngay lập tức.

**Root Cause**: Dependency conflict giữa 2 package chính.

**Fix**: Bỏ `supabase` SDK, viết REST wrapper trong `db/client.py` gọi PostgREST API trực tiếp qua `httpx`. Xem ADR-012 trong DECISIONS.md.

> ⚠️ **Phase sau lưu ý**: KHÔNG cài lại `supabase` SDK trừ khi version >= 2.10.0 (đã fix httpx conflict). Nếu cần Realtime/Auth (Phase 4), đánh giá lại thời điểm đó.

---

## 📋 Checklist test trước go-live

```
GPS:
□ Test trong văn phòng (GPS trong nhà)
□ Test đúng bán kính edge (100m từ tâm)
□ Test ngoài bán kính → phải fail
□ Test với VPN bật
□ Test phát hiện mock location (Fake GPS app)

WiFi:
□ Test với SSID đúng
□ Test với SSID sai
□ Test typo SSID
□ Test SSID có khoảng trắng/ký tự đặc biệt

QR:
□ Test scan trong 30 giây → success
□ Test scan sau 30 giây → expired message
□ Test scan QR cũ → đã dùng rồi
□ Test trên iOS (camera thường)
□ Test trên Android (camera Telegram)
□ Test trên Telegram Desktop

NFC:
□ Test trên Android (NFC bật)
□ Test trên Android (NFC tắt → hướng dẫn bật)
□ Test trên iPhone 7+ (iOS 14+)
□ Test đặt điện thoại đúng góc
□ Test gần kim loại

Manual:
□ Test gửi ảnh selfie
□ Test ảnh quá lớn
□ Test admin nhận notification
□ Test admin duyệt → user nhận confirm
□ Test admin từ chối → user nhận lý do

Scheduler:
□ Nhắc sáng đúng 8:30
□ Nhắc chiều đúng 17:30
□ Daily report đúng 9:30
□ Auto checkout 23:59
□ Không nhắc ngày nghỉ lễ

Report:
□ Excel format đúng
□ Tên nhân viên đúng
□ Giờ làm tính đúng
□ WFH hiển thị đúng
□ Nghỉ phép hiển thị đúng
```
