# DECISIONS.md — Quyết định Kiến trúc & Công nghệ

> Ghi lại lý do đằng sau các quyết định quan trọng.  
> Giúp dev mới hiểu **tại sao** chứ không chỉ **cái gì**.

---

## Format

```
## ADR-XXX: [Tiêu đề]
**Ngày**: YYYY-MM-DD
**Trạng thái**: Accepted | Deprecated | Superseded
**Context**: Vấn đề cần giải quyết
**Decision**: Quyết định chọn
**Consequences**: Ảnh hưởng (tốt và xấu)
```

---

## ADR-001: Chọn Telegram làm nền tảng chính

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Cần hệ thống chấm công cho công ty <50 người. Các lựa chọn:

- App chấm công riêng (MISA, TimeKeeper...)
- Web app riêng
- Telegram bot
- Slack bot

**Decision**: Chọn Telegram Bot + Mini App

**Lý do**:

- ✅ Nhân viên đã dùng Telegram hàng ngày → zero adoption friction
- ✅ Không cần cài app thêm
- ✅ Telegram Mini App cho phép UI đẹp mà vẫn trong Telegram
- ✅ Bot API miễn phí, không giới hạn messages
- ✅ Có thể deploy với chi phí gần 0
- ❌ Phụ thuộc vào Telegram (nếu Telegram bị chặn ở VN...)
- ❌ Không control được UI hoàn toàn như app native

**Consequences**: Toàn bộ UX phụ thuộc vào Telegram. Cần monitor nếu có thay đổi chính sách Telegram.

---

## ADR-002: Chọn Python thay vì Node.js

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Cần chọn ngôn ngữ backend cho bot.

**Decision**: Python 3.11 với `python-telegram-bot`

**Lý do**:

- ✅ `python-telegram-bot` v21 mature nhất, nhiều ví dụ
- ✅ Geopy (tính khoảng cách GPS) dễ dùng hơn nhiều
- ✅ openpyxl (Excel) ecosystem mạnh hơn
- ✅ APScheduler đơn giản và đủ dùng
- ❌ Tốc độ startup chậm hơn Node.js một chút
- ❌ Memory cao hơn nếu scale lên nhiều user

**Alternatives considered**:

- Node.js + `telegraf`: tốt nhưng team quen Python hơn
- Go: nhanh nhưng overkill và không ai quen

---

## ADR-003: Chọn Supabase thay vì MongoDB

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Cần database lưu dữ liệu chấm công có cấu trúc rõ ràng.

**Decision**: PostgreSQL qua Supabase

**Lý do**:

- ✅ Dữ liệu chấm công có quan hệ chặt (user → checkin → office) → SQL phù hợp hơn NoSQL
- ✅ Supabase free tier 500MB đủ cho 50 người × 2 năm
- ✅ Supabase có built-in REST API → Mini App có thể query trực tiếp (với RLS)
- ✅ Dashboard Supabase dễ xem data khi debug
- ✅ Backup tự động
- ❌ Supabase free tier pause project sau 1 tuần không active → cần ping định kỳ

**Workaround**: Setup cron job ping Supabase mỗi 3 ngày.

---

## ADR-004: 4 phương thức check-in dự phòng

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Một phương thức check-in duy nhất tạo single point of failure.

**Decision**: GPS → WiFi → QR → NFC → Manual (cascade fallback)

**Lý do từng phương thức**:

| Method | Ưu điểm                        | Nhược điểm                    | Vai trò     |
| ------ | ------------------------------ | ----------------------------- | ----------- |
| GPS    | Không cần setup phần cứng      | GPS trong nhà không chính xác | Primary     |
| WiFi   | Đơn giản, không cần thiết bị   | Có thể giả mạo SSID           | Primary     |
| QR     | Không thể giả mạo (expire 30s) | Cần màn hình hiển thị         | Backup      |
| NFC    | Instant, elegant               | Cần mua tag, iOS phức tạp     | Backup      |
| Manual | Luôn work                      | Cần admin duyệt               | Last resort |

**Consequences**: Phức tạp hơn để implement, nhưng UX tốt hơn nhiều khi có sự cố.

---

## ADR-005: QR Code expire 30 giây

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Cần chọn thời gian expire cho QR code.

**Decision**: 30 giây, configurable bởi admin (15s/30s/60s)

**Lý do**:

- < 15s: Quá ngắn, người scan chậm sẽ bị fail
- 30s: Đủ để mở camera, scan, và Telegram xử lý
- > 60s: Ai đó chụp ảnh QR gửi cho người khác check-in từ xa được

**30 giây là sweet spot** giữa security và usability.

---

## ADR-006: NFC dùng static token (khác QR)

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: NFC tag không thể thay đổi nội dung từ xa (khác QR).

**Decision**: NFC dùng static token, bù lại bằng GPS soft-check.

**Lý do**:

- NFC tag vật lý không thể update token động như QR
- Static token nguy cơ: ai đó chụp ảnh URL → tự check-in
- Nhưng: URL chứa `tg://` deep link → phải mở Telegram → có Telegram account → có thể trace
- Thêm GPS soft-check (warning, không bắt buộc) để phát hiện anomaly
- NFC là backup method, không phải primary → acceptable risk

---

## ADR-007: Không lưu ảnh nhân viên quá 30 ngày

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Bot nhận ảnh selfie cho manual check-in.

**Decision**: Tự động xóa ảnh sau 30 ngày, không backup.

**Lý do**:

- Tuân thủ quy định bảo vệ dữ liệu cá nhân
- Sau khi check-in đã được duyệt, ảnh không còn cần thiết
- Giảm storage cost
- Tôn trọng privacy nhân viên

**Implementation**: Cron job hàng đêm xóa ảnh > 30 ngày từ Telegram và DB.

---

## ADR-008: Không tích hợp Face Recognition ở MVP

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Face recognition có thể tăng security cho manual check-in.

**Decision**: Không implement ở MVP, để Phase 2.

**Lý do**:

- MVP cần go-live trong 4 tuần
- Face++ API cần enroll ảnh từng người → UX phức tạp khi onboard
- Privacy concern → cần policy rõ ràng hơn trước khi deploy
- 4 phương thức hiện tại đủ cho nhu cầu hiện tại
- Có thể add sau mà không break existing flow

---

## ADR-009: Gamification không phạt (no negative points)

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Thiết kế hệ thống điểm cho gamification.

**Decision**: Chỉ cộng điểm, không trừ điểm.

**Lý do**:

- Trừ điểm tạo cảm giác bị phạt → tiêu cực, ảnh hưởng tâm lý
- Nhân viên đi muộn vẫn được điểm (ít hơn) → khuyến khích check-in dù muộn
- Chấm công là việc của HR, không phải game → gamification chỉ là layer bonus
- Nếu cần phạt thật (khấu lương), đó là việc của admin, không phải bot

---

## ADR-010: Dùng Vercel + GitHub Actions thay vì Railway

**Ngày**: 2026-01 (revised)  
**Trạng thái**: Accepted  
**Thay thế**: ~~ADR-010 cũ — Railway~~

**Context**: Cần hosting cho bot Python. Ban đầu đề xuất Railway vì cần long-running process cho APScheduler.

**Insight quan trọng**: Telegram bot dùng **Webhook** — mỗi tin nhắn là một HTTP POST request độc lập. Không cần long-running process cho việc xử lý tin nhắn. Chỉ Scheduler mới cần trigger định kỳ.

**Decision**: Vercel Serverless Functions + GitHub Actions Cron

**Lý do**:

- ✅ Team đã dùng Vercel cho các dự án khác → không phải học platform mới
- ✅ GitHub Actions Cron miễn phí hoàn toàn, đủ cho mọi schedule cần thiết
- ✅ Vercel free tier đủ dùng cho <50 người (serverless invocations)
- ✅ Auto-deploy từ GitHub push — workflow quen thuộc
- ✅ Tổng chi phí: **$0/tháng**
- ❌ GitHub Actions cron tối thiểu 5 phút (không thể mỗi 30 giây)
- ❌ Vercel function timeout 10–60 giây (đủ cho bot, không đủ cho report nặng)

**Workaround nhược điểm**:

- QR expire 5 phút thay vì 30 giây — chấp nhận được cho văn phòng nhỏ
- Report nặng: paginate hoặc chạy async, gửi kết quả sau

---

## ADR-011: Không dùng Redis — QR token lưu thẳng Supabase

**Ngày**: 2026-01  
**Trạng thái**: Accepted

**Context**: Ban đầu dùng Redis (Upstash) để lưu QR token với TTL tự động.

**Decision**: Lưu QR token vào bảng `qr_sessions` trong Supabase, cleanup bằng cron.

**Lý do**:

- ✅ <50 người, tối đa vài chục QR token/ngày → Supabase xử lý nhẹ nhàng
- ✅ Bỏ một service, đơn giản hóa kiến trúc
- ✅ Không cần quản lý thêm account/credential
- ✅ Supabase index trên `expire_at` → query nhanh
- ❌ Không có TTL tự động như Redis → cần cron cleanup

**Cleanup**: GitHub Actions cron chạy mỗi đêm xóa `qr_sessions` đã hết hạn.

---

## ADR-012: Bỏ Supabase Python SDK — dùng REST API trực tiếp

**Ngày**: 2026-03-10  
**Trạng thái**: Accepted

**Context**: `supabase==2.3.0` yêu cầu `httpx==0.24.1`, nhưng `python-telegram-bot==21.5` yêu cầu `httpx~=0.27` → dependency conflict, Vercel build fail.

**Decision**: Xóa `supabase` SDK, viết lightweight REST wrapper trong `db/client.py` gọi Supabase PostgREST API trực tiếp qua `httpx`.

**Lý do**:

- ✅ `httpx` đã có sẵn qua `python-telegram-bot` → zero new dependencies
- ✅ Bundle size nhẹ hơn ~25 packages (gotrue, storage3, realtime, postgrest, supafunc)
- ✅ Cold start trên Vercel nhanh hơn → UX check-in tốt hơn
- ✅ Phase 1 chỉ cần CRUD database — PostgREST API đủ dùng
- ❌ Mất sugar syntax `.table("users").select("*").eq(...)`
- ❌ Nếu Phase 4 Mini App cần Realtime/Auth SDK → cài lại hoặc viết wrapper riêng

**Consequences**: Code gọn hơn, deploy ổn định. Khi cần Realtime subscriptions (Phase 4), đánh giá lại SDK version mới hơn (>= 2.10.0 đã fix httpx conflict).
