# agent-customer-team

> Phiên bản `0.2.0`, chưa phát hành. Bản tiếng Anh: [README.md](README.md).

## Đây là gì

Prototype hỗ trợ khách hàng chạy cục bộ, kết quả xác định, dành cho ca hỗ trợ **tổng hợp**. Công cụ kiểm ba file JSON
đầu vào (context, payload, knowledge), chọn tri thức đã duyệt trong dữ liệu thử, rồi trả một nháp trích nguyên văn hoặc
một gói chuyển người đang chờ. Repo đồng thời là plugin OpcOS: skill `customer-support-offline` bọc công cụ dòng lệnh cho
Claude Code, Codex và Antigravity. Chi tiết công cụ: [hướng dẫn ngoại tuyến](docs/offline-guide.md) (tiếng Anh).

## Giới hạn

- Chỉ dữ liệu tổng hợp; không dùng dữ liệu khách thật.
- Không mạng, không LLM, không CRM, không gửi tin; nháp không bao giờ được gửi và gói chuyển không bao giờ được nhận.
- Chưa sẵn sàng production: không bảo đảm riêng tư hay phân quyền tenant ở mức production.
- Giấy phép: MIT (xem `LICENSE`).

Cần Python 3.11 trở lên; phần chạy chỉ dùng thư viện chuẩn.

## Cài

Đưa prompt ở cuối [INSTALL.md](INSTALL.md) cho agent; agent làm theo file đó và hỏi trước khi chạm máy. Các bước theo
từng harness: [hosts/](hosts/README.md). Cài từ bản checkout cục bộ của repo (đường khuyến nghị; agent cài cũng đi đường này).

## Kiểm thử

Từ gốc repo:

```bash
python -m pytest
```

Không cần đặt biến môi trường; `pyproject.toml` đã đưa `src` vào đường nạp. `pytest-cov` là tuỳ chọn, để đo coverage; khi dùng thì đặt `COVERAGE_FILE` trỏ ra ngoài cây repo để không có file `.coverage` rơi vào repo.

GitHub Actions chạy bộ test trên Ubuntu, macOS và Windows với Python 3.11, 3.12 và 3.13 (`.github/workflows/ci.yml`).
Eval hành vi chạy riêng, khởi động tay hoặc bằng nhãn trên pull request, chấm skill với Bash trong sandbox
(`.github/workflows/eval-behavior.yml`, xem `evals-behavior/README.md`).

## Cấu trúc

| Đường | Nội dung |
|---|---|
| `src/agent_customer_team/` | công cụ ngoại tuyến (chỉ thư viện chuẩn) |
| `skills/customer-support-offline/` | skill bọc công cụ |
| `evals/` | ca thử kích hoạt skill; bộ ca kích hoạt cho `claude plugin eval` |
| `evals-behavior/`, `evals-scrub/` | bộ ca hành vi (cấp Bash, chạy trên Linux hoặc macOS) và ca canary kiểm lọc secret |
| `tests/` | test đơn vị, khoá runtime, cổng đóng gói và tài liệu |
| `.claude-plugin/`, `.codex-plugin/`, `plugin.json` | manifest plugin |
| `AGENTS.md`, `GEMINI.md` | luật của repo (cố ý không có `CLAUDE.md`; với Claude Code, cách khuyến nghị duy nhất là `.claude/CLAUDE.md` chứa `@../AGENTS.md`, điều kiện và cảnh báo ở `INSTALL.md`) |
| `hosts/`, `INSTALL.md` | hướng dẫn cài |
