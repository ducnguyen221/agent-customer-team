# Dùng agent-customer-team với Claude Code

> **Kết luận:** thêm bản checkout làm marketplace cục bộ rồi cài plugin; skill hiện với tên
> `agent-customer-team:customer-support-offline`. Áp cho Claude Code ở terminal, IDE và tab **Code** của ứng dụng Claude.

## 1. Luật

Luật nằm ở `AGENTS.md`; repo cố ý **không** có `CLAUDE.md` (để `claude plugin validate --strict` xanh). Claude Code từ bản
2.1.277 có thể tự đọc `AGENTS.md`, nhưng chỉ khi thư mục làm việc và mọi thư mục cha đều không có `CLAUDE.md`,
`.claude/CLAUDE.md` hay `CLAUDE.local.md`, và thiết lập *Project instructions* cho phép. Cách chắc chắn: tạo
`.claude/CLAUDE.md` trong bản checkout chứa đúng một dòng `@../AGENTS.md` (đường tương đối tính từ file chứa dòng `@`), hoặc
dùng đường tuyệt đối tới `AGENTS.md` trong `CLAUDE.md` bạn đang dùng. Đừng tạo lại `CLAUDE.md` ở gốc repo. Skill của plugin
chạy được mà không cần bước này.

## 2. Cài plugin

Repo chưa có remote; dùng bản checkout cục bộ (`<plugin-root>`):

```bash
claude plugin marketplace add <plugin-root>
claude plugin install agent-customer-team@agent-customer-team
```

Windows PowerShell 5.1 không mở `~` cho chương trình ngoài; dùng đường tuyệt đối trong dấu nháy kép.

Thử khi đang sửa repo, không cài: `claude --plugin-dir <plugin-root>`.

## 3. Kiểm, cập nhật, gỡ

- **Kiểm:** `claude plugin list` có `agent-customer-team`; mở phiên **mới**, nhờ phân loại một ca hỗ trợ tổng hợp từ ba
  file thử trong `tests/fixtures/` — phiên phải nạp skill rồi chạy công cụ.
- **Cập nhật:** lấy bản checkout mới, rồi `claude plugin marketplace update agent-customer-team` và
  `claude plugin update agent-customer-team@agent-customer-team`.
- **Gỡ:** `claude plugin uninstall agent-customer-team@agent-customer-team`, rồi `claude plugin marketplace remove agent-customer-team`
  (hỏi người dùng trước).
