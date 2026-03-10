# USAGE.md — Hướng dẫn sử dụng cho Nhân viên

> 📱 Tất cả chỉ cần Telegram. Không cài thêm app nào khác!
>
> 🔧 _Developers: xem chi tiết conversation flows tại [BOT_FLOWS.md](./BOT_FLOWS.md)_

---

## 🚀 Bắt đầu lần đầu (Chỉ làm 1 lần)

### Bước 1: Tìm bot

Mở Telegram, tìm kiếm: **@[TênBot]**  
Hoặc nhấn vào link: `t.me/[TênBot]`

### Bước 2: Đăng ký

```
1. Bấm START hoặc gõ /start
2. Nhập họ tên đầy đủ của bạn
3. Nhập email công ty
4. Chờ Admin duyệt (thường trong 1 giờ làm việc)
5. Nhận thông báo "Tài khoản đã được duyệt" → Sẵn sàng!
```

---

## ✅ Check-in hàng ngày

### Cách 1: Từ thông báo buổi sáng (Dễ nhất!)

```
Mỗi sáng lúc 8:30, bot sẽ nhắc bạn:
→ Bấm [🏢 Tại văn phòng] hoặc [🏠 WFH]
→ Chọn phương thức check-in
→ Done! ✅
```

### Cách 2: Gõ lệnh thủ công

```
/checkin
```

---

## 📍 4 phương thức check-in

Chọn bất kỳ phương thức nào tiện nhất. Nếu cái này không được, thử cái khác!

---

### 📍 Phương thức 1: GPS (Phổ biến nhất)

**Khi nào dùng**: Khi ở ngoài trời hoặc gần cửa sổ, GPS tốt

**Cách dùng**:

1. Bấm **[📍 Chia sẻ vị trí GPS]**
2. Telegram hỏi phép truy cập vị trí → Cho phép
3. Bấm nút **"Chia sẻ vị trí hiện tại"** (xuất hiện ở thanh dưới)
4. Bot tự động kiểm tra và xác nhận

**Mẹo**:

- Đứng gần cửa sổ hoặc ra ngoài nếu GPS yếu
- Đợi GPS lock (biểu tượng vị trí ổn định) mới gửi
- Tắt VPN nếu đang bật

---

### 📶 Phương thức 2: WiFi Văn phòng

**Khi nào dùng**: Khi đã kết nối WiFi văn phòng

**Cách dùng**:

1. Đảm bảo điện thoại đang kết nối WiFi văn phòng
2. Bấm **[📶 Check-in bằng WiFi]**
3. Nhập tên WiFi đang kết nối (vào Settings → WiFi để xem)
4. Bot kiểm tra và xác nhận

**WiFi hợp lệ của văn phòng**:

- `CompanyWiFi_2G`
- `CompanyWiFi_5G`
- `CompanyGuest`
  _(Admin sẽ thông báo danh sách cụ thể)_

---

### 📷 Phương thức 3: Quét QR Code

**Khi nào dùng**: Khi có màn hình QR ở văn phòng, hoặc GPS/WiFi không hoạt động

**Cách dùng**:

**Trên Android**:

1. Bấm **[📷 Quét QR Code]**
2. Mở camera Telegram (icon camera trong ô nhập tin)
3. Quét QR trên màn hình văn phòng
4. Tự động check-in

**Trên iPhone**:

1. Mở Camera mặc định của iPhone (không phải camera Telegram)
2. Quét QR → Telegram tự mở
3. Bot tự động check-in

> ⏱️ QR code đổi mới mỗi **5 phút**. Nếu scan không được, đợi QR mới và thử lại.

---

### 🏷️ Phương thức 4: NFC (Nhanh nhất!)

**Khi nào dùng**: Điện thoại hỗ trợ NFC, có tag NFC tại cửa văn phòng

**Kích hoạt NFC**:

- **Android**: Settings → Kết nối → NFC → Bật
- **iPhone**: iOS 14+ tự động bật, không cần làm gì

**Cách dùng**:

1. Chạm mặt sau điện thoại vào **tag NFC** (miếng dán nhỏ cạnh cửa)
2. Telegram tự mở → Bot tự động check-in
3. Xong! Cực nhanh 🚀

> 📌 Vị trí tag NFC: [Admin điền vào đây, ví dụ: "Cạnh cửa chính, cao 1.2m"]

---

### 🆘 Không check-in được bằng bất kỳ cách nào?

1. Bấm **[❓ Gặp sự cố]**
2. Chụp selfie tại văn phòng gửi bot
3. Nhập lý do ngắn gọn
4. Chờ Admin duyệt (trong vòng 30 phút giờ hành chính)

---

## 🚪 Check-out

Khi về, đừng quên check-out:

- Bấm vào thông báo nhắc lúc **17:30** → **[🚪 CHECK OUT]**
- Hoặc gõ `/checkout`

> ⚠️ Nếu quên, bot tự check-out lúc 23:59 và ghi chú "tự động".

---

## 🏠 WFH

Hôm nay làm việc ở nhà:

1. Bấm **[🏠 WFH hôm nay]** từ thông báo buổi sáng
2. Nhập ghi chú (tùy chọn)
3. Check-out khi kết thúc ngày làm việc

---

## 📅 Xin nghỉ phép

```
Gõ: /xinnghỉ
→ Chọn loại nghỉ
→ Chọn ngày
→ Nhập lý do (tùy chọn)
→ Gửi đơn → Chờ Manager duyệt
```

Bạn sẽ nhận thông báo khi đơn được duyệt hoặc từ chối.

---

## 📊 Xem lịch sử & thống kê

| Lệnh       | Chức năng                           |
| ---------- | ----------------------------------- |
| `/history` | Lịch sử 30 ngày gần nhất            |
| `/stats`   | Thống kê tháng: giờ làm, muộn, nghỉ |
| `/điểm`    | Xem điểm tích lũy & xếp hạng        |

Hoặc bấm nút **📊 Dashboard** dưới ô chat để mở Mini App với giao diện đẹp hơn.

---

## 🎮 Hệ thống điểm & xếp hạng

- Check-in **đúng giờ**: +10 điểm
- Check-in **sớm** (>15 phút): +15 điểm
- **Streak** 5 ngày liên tiếp: +20 điểm bonus
- **Streak** 10 ngày: +50 điểm bonus
- Người **đến sớm nhất** hàng ngày: +5 điểm thêm

Cuối tháng: Top 3 điểm cao nhất nhận phần thưởng từ công ty! 🏆

---

## ❓ Hỏi đáp thường gặp

**Q: Tôi quên check-in, giờ có check-in muộn được không?**  
A: Được, vẫn check-in bình thường. Bot ghi nhận thời gian thực tế.

**Q: GPS tôi cách văn phòng 150m nhưng tôi đang ở trong văn phòng?**  
A: GPS trong nhà thường không chính xác. Chuyển sang WiFi hoặc QR nhé.

**Q: Tôi dùng iPhone, NFC có hoạt động không?**  
A: Có, từ iPhone 7 trở lên (iOS 14+). Chạm phía sau điện thoại vào tag.

**Q: Check-in xong có thể sửa không?**  
A: Không tự sửa được. Nếu sai, nhắn Admin để chỉnh.

**Q: WFH có bị trừ điểm không?**  
A: Không. WFH check-in được cộng điểm bình thường (8 điểm).

**Q: Nghỉ phép có mất streak không?**  
A: Không! Nghỉ phép được duyệt sẽ bảo toàn streak của bạn.

**Q: Bot không phản hồi, làm sao?**  
A: Thử `/start` lại. Nếu vẫn không được, liên hệ Admin qua group nội bộ.

---

## 📞 Liên hệ hỗ trợ

- **Admin bot**: gõ `/help` → chọn "Liên hệ Admin"
- **Group nội bộ**: [Tên group Telegram nội bộ]
- **Email**: admin@company.com
