# Task Completion Workflow

> Chạy sau khi hoàn thành mỗi task — verify build, update docs, commit.

## Steps

### 1. Verify build/server

```bash
# Kiểm tra app chạy bình thường
timeout 5 node <entry-file> || true
```

### 2. Restart server (nếu đang chạy và có thay đổi server files)

```bash
# Kill process cũ rồi start lại
lsof -ti:<port> | xargs kill -9 2>/dev/null; sleep 1; npm run dev &
```

### 3. Kiểm tra lỗi syntax (nếu có thay đổi JS/TS)

```bash
node --check <file1> && node --check <file2>
```

### 4. Cập nhật docs nếu cần

- `CHANGELOG.md` — thêm entry vào `[Unreleased]`
- `APP_DESCRIPTION.md` — nếu thêm/xóa feature
- `KNOWN_ISSUES.md` — nếu phát hiện bug mới hoặc resolve bug cũ

### 5. Git add và commit

```bash
git add -A
git status
```

### 6. Commit với Conventional Commits format

```bash
git commit -m "<type>: <mô tả ngắn>"
```

| Type        | Mô tả                        |
| ----------- | ---------------------------- |
| `feat:`     | Tính năng mới                |
| `fix:`      | Bug fix                      |
| `docs:`     | Chỉ thay đổi tài liệu        |
| `refactor:` | Refactor, không đổi behavior |
| `chore:`    | Build, config                |
