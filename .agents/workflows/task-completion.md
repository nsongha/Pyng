---
description: Quy trình bắt buộc sau khi hoàn thành mỗi task (code, verify, commit, docs)
---

# Task Completion Workflow

## BẮT BUỘC thực hiện sau khi hoàn thành MỌI task có thay đổi code:

### 1. Test (nếu có thay đổi API/Bot code)

> **Skip nếu** task CHỈ thay đổi: `docs/`, `.agents/`, `templates/`, config files
> **Chạy nếu** có thay đổi trong `api/`, `bot/`, `config/`, `services/`, `validators/`

// turbo

```bash
# Python: kiểm tra syntax tất cả files đã thay đổi
find api/ bot/ config/ services/ validators/ -name "*.py" -newer .git/index 2>/dev/null | xargs python3 -m py_compile

# Bot: test import
python3 -c "from bot.app import create_bot; print('✅ Bot imports OK')"
```

- Đảm bảo không có syntax errors
- Test webhook health check: `curl -s https://pyng.vercel.app/api/webhook`

### 2. Verify Build (Deploy)

// turbo

```bash
# Deploy lên Vercel và kiểm tra
vercel --prod --yes
```

- Đảm bảo deploy thành công, không có build errors

### 3. Git Commit (code)

- Stage tất cả changes: `git add -A`
- Commit theo Conventional Commits format:
  - `feat:` cho tính năng mới
  - `fix:` cho bug fix
  - `refactor:` cho refactoring
  - `docs:` cho documentation only
  - `chore:` cho tooling, config
- Commit message bằng **tiếng Việt**, mô tả ngắn gọn
- Ví dụ: `feat: thêm GPS check-in với geofence validation`
- Body (optional): liệt kê các thay đổi chính, cũng bằng tiếng Việt

### 4. Documentation Update — Checklist từng file

> ⚠️ **Kiểm tra TỪNG file** trong danh sách dưới đây. KHÔNG dựa vào cảm giác "đã xong".

**Duyệt qua checklist sau và update NẾU có thay đổi liên quan:**

#### Luôn update:

- [ ] `docs/CHANGELOG.md` — luôn update khi có tính năng mới hoặc fix đáng kể
- [ ] `docs/DEV_ROADMAP.md` — tick `[x]` tasks đã xong, thêm ✅ nếu hoàn thành phase

#### Update nếu task liên quan:

- [ ] `docs/PROJECT_CONTEXT.md` — thay đổi kiến trúc, thêm service/tool, đổi deploy URL
- [ ] `docs/ARCHITECTURE.md` — thêm/sửa component, thay đổi data flow, thêm diagram
- [ ] `docs/BOT_FLOWS.md` — thêm/sửa command, thay đổi conversation flow
- [ ] `docs/TECH_STACK.md` — thêm dependency, đổi version, thêm service bên ngoài
- [ ] `docs/DEPLOYMENT.md` — thay đổi deploy process, env vars mới, infra mới
- [ ] `docs/KNOWN_ISSUES.md` — phát hiện bug mới, resolve bug cũ, thêm workaround
- [ ] `docs/DECISIONS.md` — quyết định kiến trúc/công nghệ quan trọng (WHY + tradeoff)

#### Hiếm khi thay đổi:

- [ ] `docs/PRD.md` — thay đổi scope sản phẩm lớn
- [ ] `docs/USAGE.md` — thêm tính năng mà user cần biết cách dùng
- [ ] `docs/GAMIFICATION_DESIGN.md` — thay đổi hệ thống gamification
- [ ] `docs/PRIVACY_POLICY.md` — thu thập data mới hoặc thay đổi chính sách
- [ ] `docs/README.md` — cập nhật folder structure, badges, quick start

**Nếu task chỉ là bug fix nhỏ / UI tweak → chỉ cần `CHANGELOG.md` + `DEV_ROADMAP.md`, bỏ qua các file còn lại.**

Commit docs riêng: `git commit -m "docs: ..."`

### 4.5. Verify Docs — BẮT BUỘC sau khi commit docs

> ⛔ KHÔNG được skip bước này. Đây là gate check cuối cùng trước khi báo cáo user.

// turbo

```bash
git diff HEAD~1 --name-only
```

**So sánh output với checklist bước 4:**

1. Nếu task có **tính năng mới / phase mới** → `CHANGELOG.md` + `DEV_ROADMAP.md` **BẮT BUỘC** phải xuất hiện trong diff
2. Nếu task có **bot command mới** → `BOT_FLOWS.md` phải xuất hiện
3. Nếu task có **schema change** → `ARCHITECTURE.md` phải xuất hiện

**Nếu thiếu file nào:**

- DỪNG LẠI, update file bị thiếu
- `git add` + `git commit --amend --no-edit` để gộp vào commit docs
- Chạy lại bước 4.5 để verify

### 5. Summary

- Báo cáo cho user:
  - Những gì đã làm
  - Build status
  - Files changed
  - Commit hash

## LƯU Ý QUAN TRỌNG

- KHÔNG chờ user yêu cầu mới commit — commit NGAY sau khi verify pass
- KHÔNG để changes uncommitted qua nhiều tasks
- Mỗi task = 1 commit (hoặc tối đa 2: code + docs)
- Luôn kiểm tra `git status` trước khi bắt đầu task mới
