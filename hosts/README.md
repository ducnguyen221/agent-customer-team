# hosts/ — cài và nạp theo từng harness

> **Kết luận:** luật của repo nằm ở một chỗ duy nhất — [`AGENTS.md`](../AGENTS.md) — và mỗi harness nạp nó theo cách
> riêng; skill duy nhất là `skills/customer-support-offline/`. Plugin không đòi sửa file luật cấp người dùng của harness.
> Trong các trang này `<plugin-root>` là thư mục gốc của bản checkout repo.

## Chọn harness

| Bạn chạy trong | Luật nạp bằng | Skill nạp bằng | Hướng dẫn |
|---|---|---|---|
| Claude Code (terminal, IDE, tab Code của ứng dụng Claude) | `CLAUDE.md` của repo là một dòng `@AGENTS.md` | plugin `.claude-plugin/` | [claude/README.md](claude/README.md) |
| Codex (CLI hoặc ứng dụng desktop) | tự đọc `AGENTS.md` theo chuỗi thư mục | plugin `.codex-plugin/` | [codex/README.md](codex/README.md) |
| Google Antigravity | tự đọc `AGENTS.md` và `GEMINI.md` của workspace | liên kết thư mục skill vào thư mục skill của Antigravity | [antigravity/README.md](antigravity/README.md) |
| Claude Desktop, tab chat | **chưa hỗ trợ** | — | [claude-desktop/README.md](claude-desktop/README.md) |

Cài cho người dùng: agent đọc [`INSTALL.md`](../INSTALL.md). Công cụ và giới hạn: [`docs/offline-guide.md`](../docs/offline-guide.md).

## Mốc cần phân biệt

`registered` (đã thêm marketplace) · `installed` (đã cài) · `loaded` (phiên nạp skill) · `invoked` (skill đã gọi
công cụ và có kết quả). Chỉ báo mốc đã đo; cài xong chưa chứng minh skill được nạp hay được gọi.
