# NimbusAI — Báo cáo tối ưu chi phí GPU

**Kỳ tính:** 30 ngày

**Chi phí ban đầu (baseline):** $27,133

**Chi phí sau tối ưu:** $14,626

**Projected savings (tiết kiệm dự kiến):** $12,507 (46%)

## Tiết kiệm theo từng cách

| Cách làm | Tiết kiệm (USD/tháng) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Chi phí inference trên mỗi triệu token

Cùng 7,533,027 token/ngày: baseline **$6.488/1M-token**, sau tối ưu **$1.126/1M-token**.
Phần tiết kiệm được tính lần lượt theo cascade → cache → batch, nên không đếm trùng chiết khấu:

| Cách làm | Tiết kiệm (USD/tháng) |
|---|---:|
| cascade | $1,121.96 |
| cache | $35.89 |
| batch | $53.84 |

## Nhận xét và việc cần làm

- GPU-Util lie: gpu-h100-4 util 98.2%, MFU 0.194, MBU 0.207; gpu-a10g-1 util 96.9%, MFU 0.268, MBU 0.302. GPU-Util đo mức bận, còn MFU đo FLOPs hữu ích. MBU thấp có thể gợi ý nghẽn bộ nhớ; cần profile thêm trước khi kết luận nguyên nhân và đổi GPU.
- Ưu tiên 1: kiểm tra chính sách spot/reserved cho workload đủ điều kiện (tiết kiệm khoảng $10,040/tháng); xác nhận khả năng checkpoint và thời hạn cam kết.
- Ưu tiên 2: áp dụng cascade trước, rồi cache và batch cho request chấp nhận chờ (tiết kiệm khoảng $1,212/tháng); theo dõi chất lượng và độ trễ.
- Ưu tiên 3: tắt GPU idle (khoảng $600/tháng), sau đó thử right-size trên workload có MFU thấp và đo lại throughput.
- Các khoản trên là ước tính từ mô phỏng. M3 dùng 30 ngày cho mọi job; right-size giả định giữ nguyên throughput và không cộng thêm chi phí chuyển đổi.

## Ngân sách reasoning (mở rộng)

| Nhóm | Request/ngày | Token/ngày | USD/ngày | Wh/ngày |
|---|---:|---:|---:|---:|
| Thường | 2,199 | 6,291,871 | $7.09 | 1887.6 |
| Reasoning | 201 | 1,241,156 | $1.40 | 29787.7 |

Trong 2,400 request, có 201 request bật reasoning. Nhóm này chiếm 8.4% lượt dùng, 16.5% tiền và 94.0% điện năng. Bảng giá của bài lab không tính thêm phí reasoning; tiền khác nhau do số token và model được chọn. Mức điện năng gấp 80 lần là giả định của bài, chưa phải số đo trên GPU thật.

Chỉ bật reasoning cho việc nhiều bước mà cách xử lý thường không đạt chất lượng. Nếu vượt giới hạn, chuyển bớt sang model nhỏ rồi kiểm tra lại câu trả lời.

- Cap 10% traffic: chuyển 0 request/ngày; chi phí $8.48 → $8.48/ngày, điện năng 31675.3 → 31675.3 Wh/ngày.
- Cap 5% traffic: chuyển 81 request/ngày; chi phí $8.48 → $7.76/ngày, điện năng 31675.3 → 15651.8 Wh/ngày.

Ở mức 5%, mình chuyển các request nhiều token nhất trước. Tiền chỉ giảm khi request đang dùng model lớn được chuyển sang model nhỏ. Đây là phép tính thử; chưa biết chất lượng câu trả lời sẽ đổi ra sao.

## Sustainability

- Truy vấn mẫu 800 token: 0.24 Wh, phát thải 0.091 gCO2e tại us-east-1.
- Tiền điện tại us-east-1: $0.000029/truy vấn; tại vùng sạch nhất europe-north1: $0.000022/truy vấn và 0.007 gCO2e.
- Vùng có điện rẻ nhất: us-east-wa; vùng sạch nhất: europe-north1. Chọn vùng triển khai còn phải xét độ trễ và chi phí hạ tầng; các giá điện là giả định minh họa.

_Giá và cường độ carbon là số liệu minh họa tại tháng 6/2026; cần cập nhật trước khi áp dụng thực tế._