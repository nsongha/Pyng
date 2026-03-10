# Code Review Checklist

> Checklist review code tự động trước khi commit.

## 1. Code Quality

- [ ] Không có `console.log` debug còn sót
- [ ] Không có hardcoded values (paths, URLs, credentials)
- [ ] Error handling đầy đủ (try/catch, fallback values)
- [ ] Functions không quá dài (< 50 lines)
- [ ] Naming rõ ràng, consistent (camelCase)

## 2. Security

- [ ] Không có secrets/keys trong code
- [ ] Input validation cho API endpoints
- [ ] Path traversal protection cho file operations

## 3. Performance

- [ ] Không có N+1 queries hoặc unnecessary loops
- [ ] Timeout cho external calls
- [ ] Response size hợp lý

## 4. Maintainability

- [ ] Code mới consistent với style hiện tại
- [ ] Không duplicate logic đã có
- [ ] ES Modules syntax (`import/export`)

## 5. Docs

- [ ] CHANGELOG.md cập nhật nếu có feature/fix mới
- [ ] README.md cập nhật nếu thay đổi cách dùng
