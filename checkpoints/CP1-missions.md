# CP1 — Đối chiếu kết quả M1–M4

Chạy bằng Python 3.12.14 trong `.venv` trên dữ liệu tổng hợp seed 25. Các con số dưới đây là kết quả của repo này; số trong `Guide.md` chỉ là ví dụ minh họa.

| Mission | Lệnh | Kết quả cần giữ |
|---|---|---|
| M1 | `python missions/m1_efficiency_audit.py` | `gpu-h100-4`: util 98,2%, MFU 0,194, MBU 0,207; `gpu-a10g-1`: util 96,9%, MFU 0,268. Idle waste $20/ngày, tương đương $600/tháng. |
| M2 | `python missions/m2_inference_levers.py` | 2.400 request, 7.533.027 token. Baseline $48,87/ngày và $6,488/1M-token; optimized $8,48/ngày và $1,126/1M-token; tiết kiệm 82,6%. |
| M3 | `python missions/m3_purchasing.py` | Ngưỡng reserved 55%. Có 5 job spot và 3 job reserved; $25.667 xuống $15.627/tháng, tiết kiệm 39,1%. |
| M4 | `python missions/m4_allocation.py` | Team assistant tốn nhiều nhất ($2,59/ngày). Tag coverage 92%, vượt gate 80%; `outputs/focus_export.csv` có 50 dòng dữ liệu mẫu. |

## Nhận xét để đưa vào báo cáo

- M1: GPU-Util chỉ cho biết GPU đang bận, còn MFU đo FLOPs hữu ích so với khả năng tối đa. `gpu-h100-4` bận 98,2% nhưng MFU chỉ 19,4%; có thể bị giới hạn bởi truy cập bộ nhớ hoặc overhead, song telemetry này chưa đủ để khẳng định nguyên nhân cụ thể. Idle $600/tháng bằng khoảng 2,2% baseline tổng $27.133/tháng của M5 hiện tại.
- M2: Cascade, cache và batch cộng lại giảm $40,39/ngày, hay $5,362/1M-token. Output M2 chưa tách phần đóng góp riêng của từng cách; cần đo theo thứ tự cascade → cache → batch ở CP2. Batch chỉ phù hợp request chấp nhận chờ.
- M3: Job có thể gián đoạn được chọn spot; job inference chạy thường xuyên được chọn reserved. Mô phỏng hiện dùng 30 ngày cho mọi job, dù `workloads.csv` có cột `days`; báo cáo cần ghi rõ giả định này trước khi diễn giải chi phí tháng.
- M4: Tag coverage 92% đủ mở gate chargeback của lab, nhưng 8% request còn thiếu tag cần được xử lý trước khi phân bổ toàn bộ chi phí cho team. FOCUS export hiện chỉ là mẫu 50 request đầu, không phải toàn bộ hóa đơn.

## Nguồn yêu cầu và bằng chứng

- Repo: `README.md` mục **5 Missions**; `missions/m1_efficiency_audit.py`, `m2_inference_levers.py`, `m3_purchasing.py`, `m4_allocation.py` và `outputs/focus_export.csv`.
- Lab guide: `LabGuide25.md` mục **Thực hành → Chạy năm mission**; `Guide.md` mục 4–7 yêu cầu phân tích sau từng mission.
- Không cần ảnh chụp cho CP1. Bằng chứng là output terminal đã đối chiếu với code và file FOCUS; kết quả cuối sẽ được tổng hợp vào `outputs/report.md` và bài viết nộp.
