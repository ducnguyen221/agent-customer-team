# Dùng agent-customer-team với Codex

> **Kết luận:** Codex tự đọc `AGENTS.md` khi mở thư mục repo; skill cài qua plugin từ bản checkout cục bộ. Plugin không
> sửa `~/.codex/config.toml` bằng tay: dùng đúng lệnh `codex plugin`.

## 1. Luật

Phiên mở trong thư mục repo: Codex đọc `AGENTS.md` ở gốc theo chuỗi thư mục. Không cần làm gì thêm.

## 2. Cài plugin

Cài từ bản checkout cục bộ của repo (đường khuyến nghị; agent cài cũng đi đường này), `<plugin-root>`. Lệnh plugin của Codex khác nhau theo phiên bản — xem
`codex plugin --help` trên máy trước.

```bash
codex plugin marketplace add <plugin-root>
codex plugin add agent-customer-team@agent-customer-team
```

Đóng ứng dụng Codex desktop trước khi cài, vì lệnh ghi cấu hình của Codex.

## 3. Kiểm, cập nhật, gỡ

- **Kiểm đã cài:** thư mục cache cài của Codex có `skills/customer-support-offline/SKILL.md` của plugin **và** cấu hình
  Codex có bảng `[plugins."agent-customer-team@agent-customer-team"]` (chỉ kiểm có hay không, không chép nội dung cấu
  hình). `codex plugin list` liệt kê plugin *có sẵn* trong marketplace, không phải plugin đã cài, nên không dùng nó làm
  bằng chứng đã cài.
- **Kiểm đã nạp và gọi:** phiên **mới**, nhờ phân loại một ca hỗ trợ tổng hợp từ ba file thử trong `tests/fixtures/`.
- **Cập nhật:** lấy bản checkout mới rồi cài lại theo mục 2.
- **Gỡ:** `codex plugin remove agent-customer-team@agent-customer-team`, rồi `codex plugin marketplace remove agent-customer-team`
  (hỏi người dùng trước).
