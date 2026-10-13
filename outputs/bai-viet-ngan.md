# Bài viết ngắn — Lab 25 GPU FinOps

**Phạm Đình Duy — 2A202602913**

## 1. Trước và sau khi tối ưu

Theo bài lab, chi phí ước tính cho 30 ngày giảm từ **$27.133 xuống $14.626**, tức tiết kiệm **$12.507 (46%)**. Riêng inference, cùng 7.533.027 token/ngày, giá giảm từ **$6,488 xuống $1,126 cho mỗi triệu token**. Mình dùng cùng một lượng token để so nên con số này dễ thấy hiệu quả hơn là chỉ nhìn giá thuê theo giờ của GPU.

## 2. Cách nào tiết kiệm nhiều nhất?

Thay cách mua GPU sang spot hoặc reserved là khoản lớn nhất: **$10.040/tháng**. Inference tiết kiệm thêm **$1.212/tháng**, right-size GPU đang dùng kém hiệu quả là **$655/tháng**, và tắt GPU để không là **$600/tháng**.

Trong inference, mình tính lần lượt để không cộng trùng ưu đãi: chuyển request phù hợp sang model nhỏ tiết kiệm **$1.121,96/tháng**, cache thêm **$35,89**, batch thêm **$53,84**. Vậy cascade có tác động lớn nhất trong ba cách này. Dù vậy, chỉ chuyển khi model nhỏ vẫn trả lời đủ tốt, batch cũng chỉ hợp với request có thể chờ.

## 3. GPU nào báo bận nhưng làm việc chưa hiệu quả?

`gpu-h100-4` báo bận **98,2%**, nhưng MFU chỉ **0,194**. `gpu-a10g-1` cũng báo bận **96,9%** mà MFU chỉ **0,268**. GPU-Util cho biết GPU có hoạt động, còn MFU cho biết nó dùng được bao nhiêu khả năng tính toán. Vì vậy, nhìn mỗi GPU-Util có thể khiến mình tưởng máy đang được tận dụng tốt. MBU của hai máy cũng thấp, nhưng cần đo thêm trước khi kết luận nguyên nhân là nghẽn bộ nhớ hay overhead.

Nếu chuyển hai GPU này xuống loại rẻ hơn như mô phỏng M5, khoản tiết kiệm **ước tính** là $655/tháng. Mình chưa coi đó là tiền chắc chắn lấy lại được: cần chạy thử và xem tốc độ, bộ nhớ có còn đáp ứng hay không. Ngoài ra, GPU để không làm mất **$20/ngày**, khoảng **$600/tháng**.

## 4. Hai phần mình làm thêm

**Giới hạn reasoning.** Trong 2.400 request có 201 request bật reasoning, chiếm **8,4% lượt dùng**, **16,5% tiền inference** và **94,0% điện năng** theo giả định năng lượng của bài. Giới hạn 10% hiện không giảm được gì vì traffic đã dưới mức đó. Nếu thử giới hạn 5% và chuyển 81 request nhiều token nhất sang xử lý thường, chi phí ước tính giảm **$0,72/ngày**, điện năng giảm **16.023,5 Wh/ngày**.

**Chọn vùng chạy ít phát thải.** Với 5 job có thể gián đoạn, giữ nguyên GPU và giờ chạy rồi chuyển từ `us-east-1` sang `europe-north1` làm carbon giảm từ **679.820 xuống 53.670 gCO₂e**, tức giảm **626.150 gCO₂e**. Tiền điện mô phỏng giảm từ **$214,68 xuống $161,01**. `europe-north1` sạch nhất, còn `us-east-wa` rẻ điện nhất. Trước khi chuyển thật cần phải xem độ trễ, giá thuê GPU và phí chuyển dữ liệu.

## 5. Ba việc mình sẽ làm trước

1. Kiểm tra các job có thể dùng spot hoặc reserved. Đây là khoản tiết kiệm lớn nhất, nhưng phải chắc job spot có checkpoint và cam kết reserved phù hợp.
2. Thử cascade cho request dễ, đo lại chất lượng, rồi mới bật cache và batch cho phần traffic phù hợp.
3. Tắt GPU để không; với GPU báo bận nhưng MFU thấp, đo thêm rồi thử right-size trên một workload trước khi áp dụng rộng.
