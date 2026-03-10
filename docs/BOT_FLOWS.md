# BOT_FLOWS.md — Conversation Flows

---

## 1. Đăng ký lần đầu (`/start`)

```
User: /start
Bot:  👋 Xin chào! Đây là bot chấm công của [Tên Công ty].

      Để bắt đầu, bạn cần đăng ký tài khoản.
      Vui lòng nhập họ tên đầy đủ của bạn:

User: Nguyễn Văn Minh
Bot:  Nhập email công ty của bạn:

User: minh@company.com
Bot:  ✅ Đăng ký thành công!

      Chào mừng Nguyễn Văn Minh 🎉

      Tài khoản đang chờ Admin xác nhận.
      Bạn sẽ nhận thông báo khi được duyệt.

--- [Admin nhận notification] ---

Admin Bot: 🆕 Nhân viên mới đăng ký:
           Tên: Nguyễn Văn Minh
           Email: minh@company.com
           Telegram: @username

           [✅ Duyệt]  [❌ Từ chối]

--- [Sau khi duyệt] ---

User Bot: 🎊 Tài khoản đã được duyệt!
          Bạn có thể check-in ngay hôm nay.
          Gõ /checkin để bắt đầu.
```

---

## 2. Check-in hàng ngày

### 2.1 Nhắc nhở buổi sáng (Scheduler gửi lúc 8:30)

```
Bot → User: 🌅 Chào buổi sáng, Minh!
            Hôm nay bạn làm việc ở đâu?

            [🏢 Tại văn phòng]
            [🏠 WFH hôm nay]
            [🤒 Xin nghỉ]
```

### 2.2 Check-in tại văn phòng

```
User: [Bấm 🏢 Tại văn phòng]

Bot:  Chọn phương thức check-in:

      [📍 Chia sẻ vị trí GPS]
      [📶 Check-in bằng WiFi]
      [📷 Quét QR Code]
      [🏷️ Dùng thẻ NFC]
```

### 2.3 Flow GPS

```
User: [Bấm 📍 Chia sẻ vị trí GPS]

Bot:  Nhấn nút bên dưới để chia sẻ vị trí của bạn 👇
      [📍 Chia sẻ vị trí hiện tại]    ← Keyboard button

User: [Share Location — lat: 10.7769, lng: 106.7009]

Bot:  ⏳ Đang kiểm tra vị trí...

      ✅ CHECK-IN THÀNH CÔNG!
      ━━━━━━━━━━━━━━━━━━━━
      👤 Nguyễn Văn Minh
      🕐 8:32 AM — Thứ Hai, 09/03/2026
      📍 Văn phòng HCM (cách 43m)
      🔰 Đúng giờ
      ━━━━━━━━━━━━━━━━━━━━
      🔥 Streak: 8 ngày liên tiếp
      💎 +10 điểm | Tổng: 280 điểm

      Hôm nay bạn cảm thấy thế nào?
      [🔥 Siêu năng suất] [😊 Bình thường]
      [😴 Hơi mệt]        [🆘 Cần hỗ trợ]

User: [Bấm 😊 Bình thường]

Bot:  Ghi nhận rồi! Làm việc hiệu quả nhé 💪
```

**GPS fail:**

```
Bot:  ❌ Vị trí không hợp lệ
      Cách văn phòng: 2.3 km (vượt quá giới hạn 100m)

      Thử phương thức khác?
      [📶 Check-in WiFi] [📷 Quét QR] [🏷️ NFC]
      [❓ Gặp sự cố]
```

### 2.4 Flow WiFi

```
User: [Bấm 📶 Check-in bằng WiFi]

Bot:  Nhập tên mạng WiFi bạn đang kết nối:
      (Vào Settings > WiFi để xem tên mạng)

User: CompanyWiFi_5G

Bot:  ✅ CHECK-IN THÀNH CÔNG!
      📶 WiFi: CompanyWiFi_5G ✓
      [... tương tự GPS response ...]

--- WiFi không hợp lệ ---

Bot:  ❌ WiFi "HomeNetwork" không có trong danh sách văn phòng.

      WiFi văn phòng hợp lệ:
      • CompanyWiFi_2G
      • CompanyWiFi_5G
      • CompanyGuest

      Bạn đang kết nối đúng mạng chưa?
      [🔄 Thử lại] [📍 Dùng GPS] [📷 QR] [❓ Sự cố]
```

### 2.5 Flow QR Code

```
User: [Bấm 📷 Quét QR Code]

Bot:  Mở camera và quét QR code đang hiển thị tại văn phòng.
      QR code đổi mới mỗi 5 phút ⏱️

      💡 Nếu dùng iPhone: dùng camera thường để quét,
         Telegram sẽ tự mở.

--- Sau khi scan, Telegram gửi deep link ---
--- Bot nhận: /start qr_a8f3k2p9 ---

Bot:  ✅ CHECK-IN THÀNH CÔNG!
      📷 QR Code ✓
      [... response đầy đủ ...]

--- QR hết hạn ---

Bot:  ⏰ QR code này đã hết hạn!
      Quét lại QR mới trên màn hình nhé.
```

### 2.6 Flow NFC

```
--- User chạm điện thoại vào NFC tag ---
--- Telegram tự mở với: /start nfc_HCM_MAIN ---

Bot:  ✅ CHECK-IN THÀNH CÔNG!
      🏷️ NFC — Cửa chính văn phòng HCM ✓
      [... response đầy đủ ...]
```

### 2.7 Flow Thủ công (Fallback)

```
User: [Bấm ❓ Gặp sự cố]

Bot:  Rất tiếc! Bạn đang gặp sự cố gì?

      [📍 GPS không chính xác]
      [📶 Không kết nối được WiFi VPP]
      [📷 QR không hoạt động]
      [🏷️ NFC không nhận]
      [❓ Vấn đề khác]

User: [Bấm 📍 GPS không chính xác]

Bot:  Không sao! Chụp một selfie tại văn phòng
      để admin xác nhận nhé 📸

User: [Gửi ảnh selfie]

Bot:  Nhập ghi chú (tùy chọn):

User: GPS bị lỗi, em đang ở văn phòng

Bot:  ✅ Đã gửi yêu cầu xác nhận!
      Admin sẽ duyệt sớm. Bạn sẽ nhận thông báo khi được xử lý.

--- Admin nhận ---
Bot → Admin: 🔔 Yêu cầu check-in thủ công:
             👤 Nguyễn Văn Minh
             🕐 8:45 AM
             📝 "GPS bị lỗi, em đang ở văn phòng"
             [Ảnh selfie]

             [✅ Duyệt]  [❌ Từ chối]  [💬 Nhắn tin]

--- Admin duyệt ---
Bot → User: ✅ Check-in của bạn đã được Admin duyệt!
            Thời gian ghi nhận: 8:45 AM
```

---

## 3. Check-out

```
Bot → User (17:30): 🌆 Hết giờ rồi! Đừng quên check-out nhé.
                    [🚪 CHECK OUT]

User: [Bấm CHECK OUT]

Bot:  ✅ CHECK-OUT THÀNH CÔNG!
      ━━━━━━━━━━━━━━━━━━━━
      🕐 Ra về: 17:35 PM
      ⏱️ Thời gian làm việc: 9 giờ 3 phút
      ━━━━━━━━━━━━━━━━━━━━
      Nghỉ ngơi ngon nhé! 🌙
```

---

## 4. WFH

```
User: [Bấm 🏠 WFH hôm nay]

Bot:  Xác nhận WFH hôm nay?
      Ghi chú (tùy chọn):
      [Bỏ qua]

User: Họp online cả ngày

Bot:  ✅ Đã ghi nhận WFH!
      📅 09/03/2026 — Work From Home

      Check-out khi kết thúc ngày làm việc nhé.
      [🚪 Check-out]
```

---

## 5. Xin nghỉ

```
User: /xinnghỉ   (hoặc menu)

Bot:  Xin nghỉ — chọn loại:
      [📅 Nghỉ phép năm] [💊 Nghỉ ốm]
      [🔄 Nghỉ bù]       [🚫 Không lương]

User: [Bấm 📅 Nghỉ phép năm]

Bot:  Chọn ngày bắt đầu nghỉ:
      [Chọn ngày]   ← Mini App date picker

User: 15/03/2026

Bot:  Chọn ngày kết thúc:
      [Chọn ngày]

User: 16/03/2026

Bot:  Lý do (tùy chọn):

User: Du lịch gia đình

Bot:  📋 Xác nhận đơn nghỉ phép:
      ━━━━━━━━━━━━━━━━━━━━
      Loại: Nghỉ phép năm
      Từ: 15/03 → 16/03/2026 (2 ngày)
      Lý do: Du lịch gia đình
      Số ngày phép còn lại: 8 ngày
      Sau khi nghỉ còn lại: 6 ngày
      ━━━━━━━━━━━━━━━━━━━━
      [✅ Gửi đơn]  [❌ Hủy]

User: [Gửi đơn]
Bot:  ✅ Đã gửi đơn! Chờ Manager duyệt.

--- Manager nhận ---
Bot → Manager: 📋 Đơn xin nghỉ phép:
               👤 Nguyễn Văn Minh
               📅 15–16/03/2026 (2 ngày)
               📝 Du lịch gia đình

               [✅ Duyệt]  [❌ Từ chối]  [💬 Hỏi thêm]
```

---

## 6. Lệnh Commands

### Nhân viên

| Lệnh        | Chức năng          |
| ----------- | ------------------ |
| `/checkin`  | Check-in ngay      |
| `/checkout` | Check-out          |
| `/history`  | Lịch sử 30 ngày    |
| `/stats`    | Thống kê tháng này |
| `/xinnghỉ`  | Xin nghỉ phép      |
| `/điểm`     | Xem điểm & ranking |
| `/help`     | Trợ giúp           |

### Admin

| Lệnh                         | Chức năng               |
| ---------------------------- | ----------------------- |
| `/admin`                     | Mở admin panel          |
| `/report [today/week/month]` | Báo cáo nhanh           |
| `/adduser`                   | Thêm nhân viên          |
| `/config`                    | Cài đặt hệ thống        |
| `/approve [id]`              | Duyệt check-in thủ công |

---

## 7. Admin Panel Flows

```
/admin
  │
  ├── 👥 Quản lý nhân viên
  │     ├── Danh sách nhân viên
  │     ├── Thêm nhân viên
  │     ├── Vô hiệu hóa tài khoản
  │     └── Xem lịch sử cá nhân
  │
  ├── 🏢 Cài đặt văn phòng
  │     ├── GPS Settings
  │     │     ├── Xem danh sách địa điểm
  │     │     ├── Thêm địa điểm mới → nhập tên → share location → nhập radius
  │     │     ├── Sửa bán kính → chọn địa điểm → nhập radius mới
  │     │     └── Xóa địa điểm
  │     ├── WiFi Whitelist
  │     │     ├── Xem danh sách SSID
  │     │     ├── Thêm SSID → nhập tên WiFi → nhập mô tả
  │     │     └── Xóa SSID
  │     ├── QR Settings
  │     │     ├── Xem QR hiện tại
  │     │     ├── Set thời gian expire
  │     │     └── Link màn hình QR
  │     └── NFC Settings
  │           ├── Tạo NFC token mới
  │           ├── Danh sách NFC tags
  │           └── Vô hiệu hóa tag
  │
  ├── 📊 Báo cáo
  │     ├── Hôm nay (ai có mặt / vắng / WFH)
  │     ├── Tuần này
  │     ├── Tháng này (xuất Excel)
  │     └── Tùy chọn khoảng thời gian
  │
  ├── ✅ Duyệt thủ công
  │     ├── Danh sách đang chờ
  │     ├── Duyệt từng cái
  │     └── Duyệt tất cả (bulk approve)
  │
  └── ⚙️ Cài đặt hệ thống
        ├── Giờ làm việc
        ├── Giờ nhắc check-in/out
        ├── Múi giờ
        └── Toggle tắt/bật features
```

---

## 8. Edge Cases & Xử lý

| Tình huống                    | Xử lý                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------- |
| Check-in 2 lần trong ngày     | Bot nhắc "Bạn đã check-in lúc X:XX, bấm Checkout nếu muốn ra ngoài rồi vào lại" |
| Quên check-out                | Tự động check-out 23:59, ghi chú "auto"                                         |
| GPS accuracy quá thấp (>50m)  | Cảnh báo "GPS không ổn định, thử lại hoặc dùng WiFi"                            |
| QR scan ngoài văn phòng       | Cần kết hợp GPS check hoặc admin xem xét                                        |
| Bot offline                   | QR page tự buffer, gửi lại khi bot online                                       |
| Nhân viên chưa đăng ký        | Hướng dẫn /start để đăng ký                                                     |
| Admin check-in cho người khác | `/admin → checkin_manual @username`                                             |
