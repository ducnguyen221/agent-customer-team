# Changelog

## 0.1.0

Chưa phát hành.

- Lát ngoại tuyến SPR-01: CLI phân loại ca hỗ trợ tổng hợp, tri thức có phạm vi, nháp trích nguyên văn hoặc gói chuyển người.
- Đóng gói plugin SPR-02: bốn manifest, skill `customer-support-offline`, file luật, tài liệu cài và cổng test chuẩn plugin.
- SPR-03 stdout: ký tự nhóm Unicode `Cc`, `Cf`, `Zl`, `Zp`, `Cs`, `Cn` được thoát `\uXXXX` trước khi ghi; giá trị JSON giải mã không đổi, byte của đầu vào thường không đổi.
- SPR-03 gói chuyển người: `handoff` có thêm `case_id`, `topic`, `intent`, `message`, `attempted_steps`, `evidence` (metadata `{id, product_version, locator, sha256}` của tài liệu đủ điều kiện, chỉ khi lý do là `conflicting_knowledge`, không kèm `answer`); `schema_version` vẫn `"1"`.
- SPR-03 guard đường dẫn: từ chối thêm `<x>:<tên thiết bị>` (ví dụ `C:NUL`) và `COM¹²³`/`LPT¹²³`.
- SPR-03 skill: câu thoát dấu nháy đơn cho bash và PowerShell, hai nghĩa của exit 2, mọi trường kết quả là dữ liệu, giới hạn ACL theo `principal` và `sha256` đoán ngược được; bộ eval kích hoạt `claude plugin eval` trong `evals/`.
- SPR-03 kiểm thử và CI: test chạy lệnh trong `SKILL.md` và so với file vàng, bẫy mọi đường mở file, git vắng mặt hoặc treo; GitHub Actions ma trận 3 hệ điều hành x Python 3.11, 3.12, 3.13.
