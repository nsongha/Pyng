# PRIVACY_POLICY.md — Chính sách Bảo mật & Quyền riêng tư

**Phiên bản**: 1.0  
**Hiệu lực**: 2026  
**Áp dụng cho**: Telegram Office Check-in Bot của [Tên Công ty]

---

## 1. Chúng tôi thu thập gì?

Bot thu thập các thông tin sau khi bạn sử dụng:

### 1.1 Thông tin tài khoản
- Telegram ID, username, họ tên (do bạn cung cấp khi đăng ký)
- Email công ty

### 1.2 Dữ liệu chấm công
- Thời gian check-in / check-out
- Phương thức check-in (GPS, WiFi, QR, NFC)
- Tọa độ vị trí GPS tại thời điểm check-in (nếu dùng phương thức GPS)
- Tên mạng WiFi tại thời điểm check-in (nếu dùng phương thức WiFi)

### 1.3 Dữ liệu bổ sung (tùy chọn)
- Ảnh selfie (chỉ khi dùng phương thức thủ công/manual)
- Mood (tâm trạng) do bạn tự báo cáo sau check-in
- Ghi chú khi xin nghỉ hoặc báo cáo sự cố

---

## 2. Chúng tôi KHÔNG thu thập

- ❌ Ảnh chụp màn hình hay nội dung tin nhắn cá nhân trong Telegram
- ❌ Danh sách liên hệ, ứng dụng trên điện thoại
- ❌ Dữ liệu sinh trắc học (vân tay, nhận diện khuôn mặt) ở phiên bản hiện tại
- ❌ Lịch sử duyệt web
- ❌ Thông tin tài chính, tài khoản ngân hàng
- ❌ Vị trí GPS ngoài thời điểm check-in (bot không track vị trí liên tục)

---

## 3. Chúng tôi dùng dữ liệu vào việc gì?

| Dữ liệu | Mục đích |
|---------|---------|
| Thời gian check-in/out | Tính giờ làm việc, tổng hợp bảng chấm công |
| Tọa độ GPS | Xác minh bạn đang ở văn phòng khi check-in |
| Tên WiFi | Xác minh bạn đang kết nối mạng nội bộ văn phòng |
| Ảnh selfie | Để Admin xác nhận thủ công khi các phương thức khác không hoạt động |
| Mood | Tạo báo cáo tổng hợp ẩn danh cho Manager để cải thiện môi trường làm việc |

---

## 4. Ai có thể xem dữ liệu của bạn?

| Vai trò | Dữ liệu được xem |
|---------|-----------------|
| **Bạn** | Toàn bộ lịch sử check-in của bản thân |
| **Manager** | Trạng thái check-in của team, mood tổng hợp (không xem mood cá nhân) |
| **Admin/HR** | Toàn bộ dữ liệu chấm công để tổng hợp lương, báo cáo |
| **Bên thứ ba** | **Không chia sẻ** với bất kỳ bên thứ ba nào |

---

## 5. Lưu trữ & Bảo mật

### Thời gian lưu trữ
| Loại dữ liệu | Thời gian lưu |
|-------------|--------------|
| Dữ liệu chấm công | 3 năm (theo yêu cầu pháp lý lao động VN) |
| Tọa độ GPS | 3 năm (gắn với dữ liệu chấm công) |
| Ảnh selfie (manual) | **Tối đa 30 ngày**, tự động xóa |
| Log hệ thống | 90 ngày |

### Biện pháp bảo mật
- Dữ liệu lưu trên Supabase (PostgreSQL) với Row Level Security (RLS)
- Kết nối database qua SSL/TLS
- API sử dụng JWT token có expire
- Không lưu token Telegram trong database
- Server đặt tại Singapore (SEA region, latency thấp)

---

## 6. Quyền của nhân viên

Bạn có quyền:

- **Xem**: Toàn bộ dữ liệu chấm công của bản thân (`/history`, Mini App)
- **Yêu cầu chỉnh sửa**: Nếu dữ liệu sai → nhắn Admin
- **Yêu cầu xóa**: Khi nghỉ việc, toàn bộ dữ liệu cá nhân sẽ được ẩn danh hóa (không xóa vì ảnh hưởng báo cáo lịch sử)
- **Từ chối mood tracking**: Có thể bỏ qua câu hỏi mood, không bắt buộc

---

## 7. Dữ liệu vị trí GPS — Lưu ý quan trọng

- Bot **chỉ nhận vị trí** khi bạn **chủ động** bấm "Chia sẻ vị trí" trong Telegram
- Bot **không thể** và **không** theo dõi vị trí của bạn liên tục
- Tọa độ GPS được lưu chính xác đến mức đủ xác minh bạn trong bán kính văn phòng
- Dữ liệu GPS không được dùng cho mục đích nào khác ngoài xác minh check-in

---

## 8. Tuân thủ pháp lý

Bot được thiết kế tuân thủ:
- **Luật An ninh mạng Việt Nam 2018**
- **Bộ Luật Lao động Việt Nam** (lưu trữ hồ sơ lao động)
- **Nghị định 13/2023/NĐ-CP** về bảo vệ dữ liệu cá nhân

---

## 9. Thay đổi chính sách

Nếu chính sách bảo mật thay đổi:
- Thông báo trong group Telegram nội bộ trước 7 ngày
- Bot gửi notification cho toàn bộ nhân viên
- Phiên bản và ngày cập nhật ghi rõ đầu file

---

## 10. Liên hệ

Có thắc mắc về quyền riêng tư? Liên hệ:
- Admin trong bot: `/help → Liên hệ Admin`
- Email: admin@company.com

---

*Bằng cách sử dụng bot check-in này, bạn đồng ý với chính sách trên.*  
*Việc sử dụng bot là tự nguyện trong khuôn khổ thỏa thuận lao động.*
