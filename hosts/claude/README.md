# Dùng agent-customer-team với Claude Code

> **Kết luận:** thêm bản checkout làm marketplace cục bộ rồi cài plugin; skill hiện với tên
> `agent-customer-team:customer-support-offline`. Áp cho Claude Code ở terminal, IDE và tab **Code** của ứng dụng Claude.

## 1. Luật

Luật nằm ở `AGENTS.md`; repo cố ý **không** có `CLAUDE.md` (để `claude plugin validate --strict` xanh).
Cách khuyến nghị duy nhất: trong bản checkout, tạo `.claude/CLAUDE.md` (thư mục `.claude/` đã bị git bỏ qua) chứa
đúng một dòng `@../AGENTS.md` — đường trong dòng `@` tính từ file chứa nó. Claude Code từ 2.1.277 chỉ tự đọc `AGENTS.md`
khi thư mục làm việc và mọi thư mục cha không có `CLAUDE.md`, `.claude/CLAUDE.md` hay `CLAUDE.local.md`, và thiết lập
*Project instructions* cho phép; `~/.claude/CLAUDE.md` của bạn **không** tính, nên nó không chặn việc tự đọc. **Không
khuyến nghị** dòng `@` với đường tuyệt đối: đặt trong `~/.claude/CLAUDE.md` thì luật của repo này nạp vào **mọi** dự án
bạn mở; đặt trong `CLAUDE.md` của dự án khác thì Claude Code hỏi duyệt import ngoài lần đầu, từ chối là import bị tắt.
Đừng tạo lại `CLAUDE.md` ở gốc repo. Skill của plugin chạy được mà không cần bước này.

## 2. Cài plugin

Cài từ bản checkout cục bộ của repo (đường khuyến nghị; agent cài cũng đi đường này), `<plugin-root>`:

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
