---
description: Workflow chạy sau khi hoàn thành task — verify build, update docs, commit
---

> Chạy sau khi hoàn thành mỗi task — verify, review, commit.

## 1. Verification (`verification-before-completion`)

> ⚠️ BẮT BUỘC trước khi claim "done". Invoke skill `verification-before-completion`.

- Chạy actual test/build command và **xác nhận output thành công**
- Không chỉ "assume" mọi thứ ổn — phải thấy output pass

```bash
# Python: kiểm tra syntax
python -m py_compile <file.py>

# Mini App: build check
cd miniapp && npm run build

# Bot: test import
python -c "from bot.handlers import checkin; print('OK')"
```

## 2. Code Review (`/code-review`)

- Chạy checklist `/code-review` — đảm bảo pass hết items

## 3. Cập nhật docs

### Luôn update sau mỗi task:

| File                  | Khi nào                                                           |
| --------------------- | ----------------------------------------------------------------- |
| `docs/CHANGELOG.md`   | **LUÔN** — thêm entry vào `[Unreleased]`                          |
| `docs/DEV_ROADMAP.md` | **LUÔN** — tick `[x]` tasks đã xong, thêm ✅ nếu hoàn thành phase |

### Update nếu task liên quan:

| File                      | Điều kiện                                                  |
| ------------------------- | ---------------------------------------------------------- |
| `docs/PROJECT_CONTEXT.md` | Thay đổi kiến trúc, thêm service/tool mới, đổi deploy URL  |
| `docs/ARCHITECTURE.md`    | Thêm/sửa component, thay đổi data flow, thêm diagram       |
| `docs/BOT_FLOWS.md`       | Thêm/sửa command, thay đổi conversation flow               |
| `docs/TECH_STACK.md`      | Thêm dependency, đổi version, thêm service bên ngoài       |
| `docs/DEPLOYMENT.md`      | Thay đổi deploy process, env vars mới, infra mới           |
| `docs/KNOWN_ISSUES.md`    | Phát hiện bug mới, resolve bug cũ, thêm workaround         |
| `docs/DECISIONS.md`       | Quyết định kiến trúc/công nghệ quan trọng (WHY + tradeoff) |

### Hiếm khi thay đổi (chỉ update khi có yêu cầu rõ ràng):

| File                          | Điều kiện                                      |
| ----------------------------- | ---------------------------------------------- |
| `docs/PRD.md`                 | Thay đổi scope sản phẩm lớn                    |
| `docs/USAGE.md`               | Thêm tính năng mà user cần biết cách dùng      |
| `docs/GAMIFICATION_DESIGN.md` | Thay đổi hệ thống gamification                 |
| `docs/PRIVACY_POLICY.md`      | Thu thập data mới hoặc thay đổi chính sách     |
| `docs/README.md`              | Cập nhật folder structure, badges, quick start |

## 4. Git add và commit

```bash
git add -A
git status
```

## 5. Commit với Conventional Commits (tiếng Việt)

```bash
git commit -m "<type>: <mô tả ngắn bằng tiếng Việt>"
```

| Type        | Mô tả                        |
| ----------- | ---------------------------- |
| `feat:`     | Tính năng mới                |
| `fix:`      | Bug fix                      |
| `docs:`     | Chỉ thay đổi tài liệu        |
| `refactor:` | Refactor, không đổi behavior |
| `chore:`    | Build, config                |
