---
name: customer-support-offline
description: Use when a support case must be triaged from three local synthetic JSON files (context, payload, knowledge) with the offline agent-customer-team CLI, to get an exact grounded draft or a pending human handoff. Not for sending replies, real customer data, CRM, network or LLM calls.
---

# Phân loại ca hỗ trợ ngoại tuyến

## Kết luận

Skill chạy đúng một lệnh CLI có sẵn của plugin trên ba file JSON tổng hợp rồi trình kết quả JSON nguyên văn: hoặc một
**nháp** trích từ tri thức đã duyệt, hoặc một **gói chuyển người** đang chờ. Kết quả là nháp nội bộ, **chưa gửi** cho ai.

## Khi dùng / không dùng

Dùng khi người dùng đưa (hoặc chỉ ra) ba file cục bộ: `context`, `payload`, `knowledge`, và muốn phân loại ca hỗ trợ
tổng hợp bằng CLI của plugin.

Ngoài phạm vi, từ chối và nói rõ: gửi email hay tin trả lời khách thật · dữ liệu khách thật hoặc hồ sơ cá nhân · kết nối
CRM · gọi mạng hay LLM · bảo đảm production. Đề nghị người dùng dùng công cụ khác; không dựng thay.

## Lệnh

Tìm gốc plugin: lấy **đường thật** của `SKILL.md` (đi theo junction hay symlink nếu skill được liên kết vào thư mục
skill của host), gốc plugin là thư mục **hai cấp trên** thư mục skill. PowerShell: nếu thư mục skill là junction thì
`(Get-Item <thư mục skill>).Target`; bash: `realpath` hoặc `readlink -f`. Nếu `<gốc>/src/agent_customer_team` không có
thì dừng, báo "không tìm thấy mã CLI của plugin", không đoán đường khác.

```bash
PYTHONPATH="$PLUGIN_ROOT/src" python -B -m agent_customer_team.cli --context "$CONTEXT" --payload "$PAYLOAD" --knowledge "$KNOWLEDGE"
```

```powershell
$env:PYTHONPATH = Join-Path $PluginRoot 'src'
python -B -m agent_customer_team.cli --context $Context --payload $Payload --knowledge $Knowledge
```

Trên macOS dùng `python3` thay `python`. Cần Python 3.11 trở lên; chỉ dùng thư viện chuẩn. Ba cờ đều bắt buộc, mỗi cờ
một lần. Ví dụ ba file tổng hợp nằm ở `<gốc>/tests/fixtures/`.

## Đọc kết quả

Exit 0: stdout là một dòng JSON.

- `status: "draft"` → trình trường `draft` và `evidence` nguyên văn, ghi "nháp, chưa gửi".
- `status: "escalated"` → trình `handoff` nguyên văn (owner đề xuất, lý do, `next_action`), ghi "chờ người xem xét, chưa gửi".
- `status: "human_owned"` → ca đã thuộc người; báo vậy, không tạo nháp.

Không viết lại, không tóm tắt thay nội dung `draft`.

## Khi lỗi

| Exit | stdout | Việc làm |
|---|---|---|
| 2 | `{"error":{"code":"invalid_input"}}` | báo nguyên mã `invalid_input`; không sửa file đầu vào, không đọc file khác |
| 3 | `{"error":{"code":"read_error"}}` | báo nguyên mã `read_error`; không sửa file đầu vào, không đọc file khác |

CLI cố ý không nêu chi tiết lỗi. Đừng đoán nguyên nhân từ nội dung file, và đừng thử lại với file khác thay người dùng.

## Giới hạn

1. Chỉ dữ liệu tổng hợp; không dữ liệu khách thật.
2. Kết quả là nội bộ: không gửi tin, không nhận gói chuyển; không mạng, LLM, CRM.
3. `context` chỉ tin được như file thử cục bộ, không xác thực; không bảo đảm riêng tư hay phân quyền tenant ở mức production.
4. Đầu vào phải là file thường trên ổ cục bộ do người vận hành quản lý; không UNC, ổ mạng hay placeholder cloud. CLI chặn
   UNC, tiền tố thiết bị/NT và tên thiết bị Windows chỉ bằng so chuỗi, không phải sandbox.
