# Dùng agent-customer-team với Google Antigravity

> **Kết luận:** Antigravity tự nạp `AGENTS.md` và `GEMINI.md` của workspace; skill nạp bằng cách liên kết **một** thư mục
> `skills/customer-support-offline/` vào thư mục skill của Antigravity.

## 1. Luật

Phiên mở trong thư mục repo: Antigravity nạp `AGENTS.md` và `GEMINI.md` theo chuỗi thư mục. `GEMINI.md` của repo cố ý
chỉ là con trỏ văn xuôi tới `AGENTS.md` để không nạp đúp.

## 2. Skill

Thư mục skill toàn cục là `~/.gemini/antigravity/skills/`. Tạo một liên kết thư mục tên `customer-support-offline` trỏ
về `skills/customer-support-offline/` của bản checkout (`<plugin-root>`): Windows dùng junction (không cần Developer
Mode), macOS dùng symlink. Không chép thư mục: chép là có bản thứ hai và hai bản sẽ trôi khỏi nhau; skill còn cần tìm
mã công cụ ở `src/` qua đường thật của liên kết.

- Tên thư mục đã có sẵn ở đích: **không ghi đè**, báo người dùng chọn.
- Thử nhanh không liên kết gì: mở thẳng repo làm workspace; agent đọc `skills/customer-support-offline/SKILL.md`.

## 3. Kiểm, cập nhật, gỡ

- **Kiểm:** phiên **mới**, nhờ phân loại một ca hỗ trợ tổng hợp từ ba file thử trong `tests/fixtures/`; skill phải tìm
  được `src/agent_customer_team` qua liên kết rồi chạy công cụ.
- **Cập nhật:** lấy bản checkout mới — liên kết tự thấy bản mới.
- **Gỡ:** xoá đúng **liên kết** do mình tạo, không xoá thư mục đích của liên kết (hỏi người dùng trước).
