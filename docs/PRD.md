# PRD — Product Requirements Document

**Dự án**: Telegram Office Check-in Bot  
**Công ty**: BSMlabs  
**Phiên bản**: 1.0  
**Cập nhật**: 2026  
**Trạng thái**: Draft

---

## 0. Thông tin BSMlabs

|                  |                                                            |
| ---------------- | ---------------------------------------------------------- |
| **Văn phòng**    | BSMlabs Office — 219 Trung Kính, Yên Hòa, Cầu Giấy, Hà Nội |
| **Giờ làm việc** | 08:45 — 17:45 (T2–T6)                                      |
| **Quỹ đi muộn**  | Tổng **3 tiếng/tháng** (180 phút), tự động trừ dần         |
| **WFH**          | Tối đa **2 lần/tháng**, cần khai trước                     |
| **Quy mô**       | <50 nhân viên                                              |

---

## 1. Mục tiêu sản phẩm

### 1.1 Tầm nhìn

Xây dựng hệ thống chấm công hiện đại, không ma sát (zero-friction), hoàn toàn qua Telegram — không cần cài thêm app, không cần phần cứng đắt tiền, phù hợp văn hóa startup trẻ.

### 1.2 Mục tiêu đo được (OKRs)

| Mục tiêu     | Chỉ số                                 | Target          |
| ------------ | -------------------------------------- | --------------- |
| Adoption     | % nhân viên dùng mỗi ngày              | >90% sau tuần 2 |
| Accuracy     | Tỷ lệ check-in hợp lệ (không gian lận) | >99%            |
| Satisfaction | Khảo sát hài lòng nhân viên            | >4/5 sao        |
| Admin effort | Thời gian HR xử lý chấm công/tuần      | <30 phút        |

---

## 2. Người dùng (Personas)

### 👤 Nhân viên (Employee)

- Độ tuổi: 22–35, quen dùng smartphone
- Kỳ vọng: nhanh, không phiền, dùng app sẵn có
- Nỗi đau: phải mở app riêng, nhớ check-out, không biết mình đã đủ giờ chưa

### 👔 Admin / HR

- Cần: xem báo cáo dễ, cấu hình linh hoạt, xử lý ngoại lệ nhanh
- Nỗi đau: tổng hợp chấm công thủ công mỗi tháng, giải quyết khiếu nại

### 👩‍💼 Manager

- Cần: biết ai có mặt hôm nay, ai đang WFH, team mood thế nào
- Nỗi đau: phải hỏi HR mỗi khi cần thông tin

---

## 3. Phương thức Check-in

### 3.1 GPS Geofence (Primary)

**Mô tả**: Nhân viên share location trong Telegram, bot kiểm tra trong bán kính cho phép.

**Yêu cầu chức năng**:

- Admin cài đặt tọa độ trung tâm văn phòng (lat/lng) qua lệnh bot
- Admin cài range bán kính: 50m / 100m / 200m / custom (mét)
- Hỗ trợ **nhiều địa điểm** (multi-office): mỗi địa điểm có tên và bán kính riêng
- Bot trả về kết quả kèm khoảng cách thực tế: "✅ Hợp lệ — cách văn phòng 45m"
- Phát hiện location giả: kiểm tra tốc độ di chuyển bất thường (>500km/h = fake)
- Accuracy threshold: chấp nhận GPS accuracy ≤ 50m, nếu >50m cảnh báo nhân viên

**Cấu hình Admin**:

```
/admin → Cài đặt văn phòng → GPS Settings
  - Thêm địa điểm mới
  - Sửa bán kính
  - Xóa địa điểm
  - Xem danh sách địa điểm
```

### 3.2 WiFi Nội bộ (Primary)

**Mô tả**: Nhân viên gửi tên WiFi đang kết nối, bot đối chiếu với danh sách whitelist.

**Yêu cầu chức năng**:

- Admin quản lý whitelist SSID (tên WiFi) qua bot
- Hỗ trợ nhiều SSID (nhiều bộ phát, nhiều tầng)
- Bot yêu cầu nhân viên chụp screenshot WiFi settings hoặc nhập tên SSID
- Không xác minh được SSID 100% qua Telegram API → kết hợp với timestamp + user history để phát hiện bất thường
- Lưu MAC address router (nếu có thể lấy qua Mini App)

**Lưu ý bảo mật**: WiFi có thể bị giả mạo tên → đây là phương thức tiện nhưng không phải high-security. Kết hợp với GPS nếu cần độ chính xác cao.

**Admin Config**:

```
/admin → WiFi Settings
  - Thêm SSID vào whitelist
  - Xóa SSID
  - Xem danh sách SSID được phép
```

### 3.3 QR Code Động (Backup)

**Mô tả**: Màn hình tại văn phòng hiển thị QR code thay đổi mỗi 5 phút. Nhân viên scan → check-in.

**Yêu cầu chức năng**:

- QR code chứa token ngẫu nhiên + timestamp, expire sau **5 phút** (giới hạn bởi GitHub Actions Cron tối thiểu 5 phút, chấp nhận được cho văn phòng nhỏ <50 người)
- Bot tạo và refresh QR tự động, display trên màn hình văn phòng (hoặc TV/tablet)
- Nhân viên dùng camera Telegram scan QR → bot nhận token → validate → check-in
- Admin có thể điều chỉnh thời gian expire: 1 phút / 5 phút / 10 phút
- Giao diện hiển thị QR: trang web đơn giản `/qr-display` (auto-refresh)
- Hỗ trợ nhiều QR cho nhiều cửa/địa điểm

### 3.4 NFC Tag (Backup)

**Mô tả**: Tag NFC dán tại cửa văn phòng. Nhân viên chạm điện thoại → mở link → check-in qua bot.

**Yêu cầu chức năng**:

- NFC tag chứa deep link `tg://resolve?domain=BotName&start=nfc_TOKEN`
- Khi chạm: Telegram mở ra, bot nhận token, validate, check-in tự động
- Token trong NFC là **static** (khác QR) — bù lại bằng cách verify bằng GPS đồng thời
- Admin cấu hình và in/ghi NFC tag qua lệnh `/admin → NFC Settings → Tạo NFC token`
- Hỗ trợ Android (Web NFC API) và iOS (iOS 14+ NFC background reading)

### 3.5 Fallback Thủ Công

**Khi nào dùng**: GPS fail, không có WiFi văn phòng, không có QR, NFC hỏng.

**Quy trình**:

1. Nhân viên bấm "Gặp sự cố check-in"
2. Chụp selfie gửi bot (với metadata timestamp)
3. Nhập lý do
4. Admin nhận notification → Duyệt / Từ chối trong bot
5. Có thể duyệt hàng loạt (bulk approve)

---

## 4. Tính năng Check-out

- Nhân viên check-out khi ra về (tương tự check-in, đơn giản hơn)
- Bot nhắc check-out nếu đến 18h chưa check-out
- Tự động check-out lúc 23:59 nếu quên (ghi chú: auto check-out)
- Tính giờ làm việc = check-out − check-in

---

## 5. Quản lý của Admin

### 5.1 Cấu hình hệ thống

- Set múi giờ (mặc định: Asia/Ho_Chi_Minh)
- Set giờ làm việc chuẩn: **08:45 – 17:45**
- Set thời gian nhắc check-in: **08:30** (trước 15 phút)
- Set thời gian nhắc check-out: **17:45**
- Toggle bật/tắt từng phương thức check-in
- Cấu hình geofence, WiFi whitelist, NFC token
- Cấu hình quỹ đi muộn và giới hạn WFH

### 5.2 Quản lý nhân viên

- Thêm/xóa nhân viên
- Gán role: Employee / Manager / Admin
- Xem lịch sử check-in của từng người
- Export dữ liệu chấm công ra Excel

### 5.3 Báo cáo

- **Daily**: danh sách ai có mặt, ai vắng, ai WFH → gửi vào group HR lúc 9:30 AM
- **Weekly**: tổng giờ làm, muộn, nghỉ của từng người
- **Monthly**: bảng chấm công đầy đủ (Excel), tổng hợp cho lương
- **Real-time**: `/report today` bất cứ lúc nào

---

## 6. WFH & Nghỉ phép

### 6.1 WFH — BSMlabs Policy

- Mỗi nhân viên được WFH tối đa **2 lần/tháng**
- Cần khai WFH **trước** khi check-in (không khai sau)
- Bot tự đếm số lần WFH đã dùng trong tháng hiện tại
- Khi đã dùng hết 2 lần: bot thông báo và yêu cầu xin phép admin
- Manager xem được ai đang WFH hôm nay trong dashboard

### 6.2 Quỹ thời gian đi muộn — BSMlabs Policy

- Mỗi nhân viên có **180 phút (3 tiếng) đi muộn/tháng**
- Cách tính: check-in sau 08:45 → số phút muộn trừ vào quỹ
- Grace period: **5 phút** (đến trước 08:50 không tính muộn)
- Khi quỹ còn ≤ 30 phút: bot cảnh báo nhân viên
- Khi quỹ hết: bot thông báo và báo admin
- Quỹ **reset về 180 phút** vào ngày 1 hàng tháng
- Admin có thể điều chỉnh quỹ thủ công cho từng người

```
Bot sau khi check-in muộn:
⏰ Check-in: 09:10 (muộn 25 phút)
📊 Quỹ muộn tháng 3: 180 → 155 phút còn lại
⚠️ Còn 155 phút trong tháng này
```

### 6.3 Các loại Request — BSMlabs

Nhân viên có thể gửi các request sau qua bot, Manager/Admin duyệt:

| Loại Request                | Mô tả                            | Người duyệt |
| --------------------------- | -------------------------------- | ----------- |
| 🏠 **WFH**                  | Làm việc từ xa                   | Manager     |
| 📅 **Nghỉ phép năm**        | Annual leave                     | Manager     |
| 💊 **Nghỉ ốm**              | Sick leave                       | Manager     |
| 🔄 **Nghỉ bù**              | Compensatory leave               | Manager     |
| 🚫 **Nghỉ không lương**     | Unpaid leave                     | Admin       |
| ⏰ **Xin về sớm**           | Early leave, ghi nhận giờ        | Manager     |
| 🌙 **Xin làm thêm giờ**     | Overtime, ghi nhận để tính bù    | Manager     |
| ✏️ **Điều chỉnh chấm công** | Sửa check-in sai                 | Admin       |
| 🏢 **Công tác**             | Business trip, miễn check-in GPS | Admin       |
| 📋 **Ý kiến / Phản hồi**    | Gửi feedback cho HR              | Admin       |

**Flow chung của Request**:

```
Nhân viên gửi request → Manager/Admin nhận notification
→ [Duyệt / Từ chối / Hỏi thêm]
→ Nhân viên nhận kết quả
→ Hệ thống tự cập nhật chấm công
```

---

## 7. Non-functional Requirements

| Yêu cầu         | Tiêu chí                                                 |
| --------------- | -------------------------------------------------------- |
| **Hiệu năng**   | Phản hồi check-in < 2 giây                               |
| **Uptime**      | >99% trong giờ hành chính (7–19h)                        |
| **Bảo mật**     | Không lưu ảnh nhân viên quá 30 ngày                      |
| **Scalability** | Hỗ trợ tới 200 nhân viên mà không cần thay đổi kiến trúc |
| **Privacy**     | Tuân thủ Luật An ninh mạng VN, có Privacy Policy rõ ràng |
| **Offline**     | Khi bot down: QR page vẫn chạy, data buffer trong 1h     |

---

## 8. Out of Scope (MVP)

- Tích hợp phần mềm kế toán/lương
- Chấm công bằng khuôn mặt (face recognition) — Phase 2
- Multi-company (SaaS mode) — Phase 3
- Mobile app riêng
- Tích hợp calendar (Google Cal, Outlook) — Phase 2
