# GAMIFICATION_DESIGN.md — Hệ thống Game hóa

---

## 1. Triết lý thiết kế

> **Mục tiêu**: Biến việc check-in từ "nghĩa vụ" thành "thói quen vui".  
> **Nguyên tắc**: Không phạt, chỉ thưởng. Tạo cạnh tranh lành mạnh, không áp lực.

---

## 2. Hệ thống điểm

### 2.1 Nguồn điểm

| Hành động | Điểm | Ghi chú |
|-----------|------|---------|
| Check-in đúng giờ | +10 | Trước hoặc đúng giờ làm |
| Check-in sớm (≥15 phút) | +15 | Early bird bonus |
| Check-in muộn (≤30 phút) | +5 | Vẫn được điểm, giảm |
| Check-in muộn (>30 phút) | +2 | Khuyến khích vẫn check-in |
| Check-out đúng giờ | +5 | |
| WFH check-in | +8 | Hơi thấp hơn onsite |
| Streak bonus 5 ngày | +20 | Cộng thêm vào ngày thứ 5 |
| Streak bonus 10 ngày | +50 | |
| Streak bonus 20 ngày | +100 | |
| Streak bonus 30 ngày | +200 | |
| Mood tốt (Great/Good) | +2 | Khuyến khích báo cáo thật |
| Người đầu tiên đến | +5 | 🥇 Badge hàng ngày |
| Top 3 đến sớm nhất | +3 | 🥈🥉 |

### 2.2 Không trừ điểm
Hệ thống **không trừ điểm** khi:
- Nghỉ phép, nghỉ ốm
- Check-in muộn
- WFH

Triết lý: Điểm là phần thưởng, không phải hình phạt.

---

## 3. Streak System

### 3.1 Định nghĩa streak
- **Streak** = số ngày làm việc liên tiếp có check-in hợp lệ
- WFH hợp lệ cũng tính streak
- Nghỉ phép được duyệt: **bảo toàn streak** (không reset)
- Nghỉ không phép: **reset streak về 0**
- Cuối tuần (T7, CN): **không tính vào streak**

### 3.2 Streak milestones

```
🔥 1-4 ngày     → "Đang khởi động"
🔥🔥 5-9 ngày   → "Vào guồng rồi!" (+20 pts)
🔥🔥🔥 10-19    → "Ổn định" (+50 pts)
⚡ 20-29 ngày   → "Chuyên nghiệp!" (+100 pts)
💎 30+ ngày     → "Huyền thoại" (+200 pts)
```

### 3.3 Streak reminder
```
Bot (T7 tối): 🔥 Streak của bạn đang là 12 ngày!
              Thứ 2 tới đừng quên check-in nhé 
              để giữ streak nhé! 💪
```

---

## 4. Badges (Huy hiệu)

| Badge | Điều kiện | Icon |
|-------|-----------|------|
| Early Bird | Đến sớm ≥5 lần | 🐦 |
| Punctual Pro | 20 ngày đúng giờ liên tiếp | ⏰ |
| Streak Master | Streak 30 ngày | 🏆 |
| Social Butterfly | Check-in cùng 5 đồng nghiệp | 🦋 |
| Night Owl | Check-out sau 20:00 (3 lần) | 🦉 |
| Comeback Kid | Reset streak → rebuild lên 10 | 💪 |
| Mood Booster | Mood "Great" 10 lần liên tiếp | 🌟 |
| First Blood | Người đầu tiên check-in ngày | 🥇 |
| Iron Man | Check-in đủ cả tháng | 🦾 |

---

## 5. Leaderboard

### 5.1 Bảng xếp hạng hàng tháng
```
Bot gửi hàng tuần (thứ 2):

🏆 BẢNG XẾP HẠNG TUẦN 11 — Tháng 3/2026
━━━━━━━━━━━━━━━━━━━━
🥇 Nguyễn Văn Minh    — 342 pts 🔥 18
🥈 Trần Thị Lan       — 298 pts 🔥 15
🥉 Lê Hoàng Nam       — 276 pts 🔥 12
4. Phạm Thu Hà        — 243 pts
5. Đặng Quốc Việt     — 221 pts
...
━━━━━━━━━━━━━━━━━━━━
Bạn đang ở vị trí #7 — 198 pts 🔥 8
Cách top 5: 23 điểm 👆 Come on!
```

### 5.2 Các loại leaderboard
- **Tháng này**: Reset mỗi tháng, có quà
- **Streak hiện tại**: Ai đang giữ streak dài nhất
- **All-time**: Tổng điểm từ trước tới giờ (danh dự)
- **Department**: Nếu có nhiều phòng ban

---

## 6. Phần thưởng (Rewards)

Admin có thể cài đặt phần thưởng tháng:

| Hạng | Gợi ý phần thưởng |
|------|-------------------|
| 🥇 Top 1 | Thẻ quà tặng 500k, ngày nghỉ thêm, ưu tiên chọn giờ |
| 🥈 Top 2 | Thẻ quà tặng 300k, cà phê văn phòng tháng miễn phí |
| 🥉 Top 3 | Thẻ quà tặng 200k |
| Iron Man (đủ tháng) | Badge đặc biệt + 100k |

> 💡 Gợi ý: Announce phần thưởng vào đầu tháng để tạo động lực.

---

## 7. Mood Tracking

### 7.1 Câu hỏi mood
Sau mỗi check-in buổi sáng:
```
Hôm nay bạn cảm thấy thế nào?
[🔥 Siêu năng suất]  [😊 Bình thường]
[😴 Hơi mệt]         [🆘 Cần hỗ trợ]
```

### 7.2 Dữ liệu mood cho Manager

Manager nhận **weekly mood summary** (ẩn danh theo nhóm):

```
📊 MOOD REPORT — Tuần 11
━━━━━━━━━━━━━━━━━
🔥 Siêu năng suất:  12% (↑ 3%)
😊 Bình thường:     58%
😴 Hơi mệt:        24% (↑ 8% ⚠️)
🆘 Cần hỗ trợ:     6% (2 người)
━━━━━━━━━━━━━━━━━
⚠️ "Hơi mệt" tăng đáng kể tuần này.
   Xem xét workload của team nhé.
```

### 7.3 Cảnh báo burnout
Nếu cùng một người báo cáo "Cần hỗ trợ" 3 ngày liên tiếp:
```
Bot → Manager (private): 
⚠️ [Tên nhân viên] đã báo cáo "Cần hỗ trợ" 3 ngày liên tiếp.
Bạn có muốn liên hệ với họ không?
[💬 Nhắn tin ngay] [📅 Đặt lịch 1:1] [Bỏ qua]
```

---

## 8. Thông báo đặc biệt

### Ngày sinh nhật
```
Bot → All: 🎂 Hôm nay là sinh nhật của Nguyễn Văn Minh!
           Chúc mừng sinh nhật! 🎉
           [🎁 Gửi lời chúc]
```

### Kỷ niệm
```
Bot → User: 🎊 Hôm nay là tròn 1 năm bạn join [Company]!
            Cảm ơn vì đã đồng hành 🙏
            Bạn đã check-in tổng cộng 247 lần.
```

### Streak bị reset
```
Bot → User: 😢 Ôi! Streak 15 ngày của bạn đã bị reset.
            Đừng nản lòng! Hãy bắt đầu lại từ hôm nay 💪
            /checkin để khởi động chuỗi mới!
```

---

## 9. Cài đặt Gamification (Admin)

Admin có thể tùy chỉnh:
```
/admin → Gamification Settings
  - Bật/tắt toàn bộ hệ thống điểm
  - Điều chỉnh số điểm từng hành động
  - Cài đặt phần thưởng tháng
  - Xuất báo cáo điểm (Excel)
  - Reset điểm (đầu năm mới)
  - Tặng điểm thủ công cho nhân viên
```
