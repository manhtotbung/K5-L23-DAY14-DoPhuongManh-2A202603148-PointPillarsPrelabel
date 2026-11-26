# Báo cáo Day 14 — Đỗ Phương Mạnh — 2A202603148

- Mã học viên dùng với `--student`: `148`
- `seed_tag` trong `frames_A.txt`: `393590736f`

## 1. Dự đoán trước sweep (bước 5b)

- Tham số tôi nghĩ giảm công sửa nhiều nhất: `score_thr` (tăng từ `0.1` lên khoảng `0.4`–`0.5`), tác động lớn hơn nhiều so với `min_points`.
- Vì sao (nhìn ảnh BEV tập A: box thừa nhiều hay box sót nhiều?):
  - Trên ảnh 7 camera + BEV tập A (`s01f33`, `s03f00`, `s05f03`) và số đo cấu hình gốc (GT 33, dự đoán 84: **xóa 52, thêm 1, sửa 8 → chi phí 20.6**), nguồn chi phí áp đảo là **box thừa** (`52 × 0.3 = 15.6`, chiếm hơn 75% tổng chi phí), còn box sót chỉ có 1 (xe tải nhẹ trắng ở `s03f00`).
  - Các box thừa tập trung ở dải phân cách/bụi cây đỏ, hàng xe đạp/xe máy không người dựng trên vỉa hè, tường tôn công trường và chính xe ego (`d < 1.5 m`). Quan sát point cloud cho thấy phần lớn các box nhiễu này vẫn chứa hàng chục đến vài trăm điểm LiDAR (nhiều hơn hẳn ngưỡng `min_points=5` hay `10`), nên `min_points` khó loại bỏ được chúng.
  - Ngược lại, đa số box thừa có `score` thấp (khoảng `0.21`–`0.45`), trong khi hầu hết phương tiện thật có `score` cao hơn (`0.45`–`0.96`). Do đó nâng `score_thr` lên mức trung bình–cao (khoảng `0.4`–`0.5`) kỳ vọng sẽ giảm mạnh số box phải xóa, dù cần lưu ý đánh đổi: nếu nâng quá cao (`0.5`) có thể làm rơi một vài xe thật có điểm tin cậy thấp (`0.27`–`0.45` như xe tải xanh phía sau ở `s05f03`, xe van ở `s03f00`, hay xe tải ngược chiều ở `s01f33`), mà mỗi box bị rơi tốn `1.0` điểm thêm trong khi mỗi box thừa chỉ tiết kiệm được `0.3` điểm xóa.

## 2. Tập A: sửa tay và tune

| Cấu hình | Xóa | Thêm | Sửa | Chi phí |
|---|---:|---:|---:|---:|
| Gốc | 52 | 1 | 8 | 20.6 |
| `best_config.json` | 13 | 8 | 5 | 14.4 |

- Tham số đã đổi trong `best_config.json`: `score_thr: 0.1 -> 0.5` (giữ nguyên `min_points=0` và các tham số còn lại; tại `score_thr=0.5`, cả 3 mức `min_points=0, 5, 10` cho cùng kết quả `14.40`).
- Kết quả leave-one-out (dán các dòng `scripts/pp_sweep.py` in ra):
  ```text
  Leave-one-out (chọn trên các frame còn lại, chấm trên frame bỏ ra):
    s01f33: cấu hình chọn {'score_thr': '0.4', 'min_points': '0'} → 3.7 (tốt nhất có thể 1.9)
    s03f00: cấu hình chọn {'score_thr': '0.5', 'min_points': '0'} → 5.6 (tốt nhất có thể 4.0)
    s05f03: cấu hình chọn {'score_thr': '0.5', 'min_points': '0'} → 6.9 (tốt nhất có thể 6.1)
  ```
- Cấu hình có ổn định trên từng frame không? Vì sao tôi vẫn chọn (hoặc không chọn) nó:
  - Cấu hình **không hoàn toàn ổn định** giữa từng frame: khi bỏ `s01f33` ra, 2 frame còn lại chọn `score_thr=0.4` (chấm trên `s01f33` ra `3.7`, cao hơn mức tốt nhất `1.9` của `score_thr=0.5`); ngược lại, khi bỏ `s03f00` ra, 2 frame kia chọn `score_thr=0.5` nhưng chấm trên `s03f00` ra `5.6` (thậm chí **tăng** so với mức gốc `4.3` và mức tốt nhất `4.0` của `score_thr=0.3`).
  - Nguyên nhân là mật độ cảnh khác nhau rõ rệt: `s01f33` là đường thoáng nhưng có rất nhiều box nhiễu ở bụi cây/xe đạp dựng bên đường (27 box thừa ở cấu hình gốc) nên `score_thr=0.5` giảm chi phí mạnh (`8.6 -> 1.9`), trong khi `s03f00` là hàng xe đông trong làn có ít box thừa (6 box) nhưng có vài xe bị che khuất/ở xa mang `score` `0.27–0.44` nên ngưỡng `0.5` làm rơi xe thật.
  - Tôi vẫn dùng `best_config.json` (`score_thr=0.5, min_points=0`) cho tập B vì đây là cấu hình đạt tổng chi phí thấp nhất trên toàn bộ tập A (`14.4` vs `15.0` ở `0.4` và `20.6` ở gốc), giảm 39 box thừa trên tập A và giúp giảm đáng kể nhiễu bụi cây/vỉa hè trước khi sửa tay 12 frame tập B.

## 3. Trước/sau (bước 8)

![so sánh](../../d14_148/compare/s05f03.jpg)

*(Các ảnh đầy đủ cho cả 3 frame nằm trong `d14_148/compare/s01f33.jpg`, `s03f00.jpg` và `s05f03.jpg`.)*

- `scripts/pp_compare.py` báo giảm **30%** công sửa trên tập A (từ **20.6** xuống **14.4**; theo từng frame: `s01f33`: `8.6 -> 1.9`, `s03f00`: `4.3 -> 5.6`, `s05f03`: `7.7 -> 6.9`).
- Dự đoán ở mục 1 đúng hay sai? Giải thích bằng số box xóa/thêm/sửa:
  - **Đúng về hướng tác động của tham số và đúng về đánh đổi đã cảnh báo**, cụ thể:
    1. `score_thr` đúng là tham số duy nhất tạo khác biệt lớn: nâng `score_thr` từ `0.1 -> 0.5` kéo số box cần **xóa** từ `52 -> 13` (giảm 39 box, tiết kiệm `39 × 0.3 = 11.7` điểm) và số box cần **sửa** từ `8 -> 5` (tiết kiệm `1.5` điểm).
    2. `min_points` đúng như dự đoán là hầu như không có tác dụng: ở `score_thr=0.1` chỉ giảm từ `20.6 -> 20.0` khi tăng `min_points` lên `10`, còn từ `score_thr >= 0.3` trở lên cả ba mức `0, 5, 10` cho chi phí hoàn toàn giống nhau vì các box nhiễu trên bụi cây/hàng xe dựng đều có trên 10 điểm LiDAR.
    3. Rủi ro đánh đổi đã dự đoán cũng xảy ra đúng thực tế: số box phải **thêm** tăng từ `1 -> 8` (`+7.0` điểm), nhìn thấy rõ qua các hộp màu xanh dương xuất hiện ở nửa phải của `s05f03.jpg` (xe tải xanh lớn phía sau và 2 xe ở xa phía trước bị rớt dưới ngưỡng `0.5`) và khiến riêng frame `s03f00` tăng chi phí từ `4.3 -> 5.6`. Tuy nhiên nhờ giảm mạnh 39 box thừa, tổng chi phí trên 3 frame vẫn giảm `6.2` điểm (`-30%`).

## 4. Tập B

Số đo từ `scripts/pp_prelabel.py --frames d14_148/frames_B.txt --config d14_148/best_config.json --gt d14_148/ref_B.json`:

| Xóa | Thêm | Sửa | Chi phí |
|---:|---:|---:|---:|
| 43 | 31 | 3 | 45.4 |

*(Tổng trên 12 frame tập B: GT `153`, dự đoán `165`, khớp `122`; chi phí `0.3×43 + 1.0×31 + 0.5×3 = 12.9 + 31.0 + 1.5 = 45.4`.)*

- Loại box tốn công sửa nhất ở tập B:
  - Nhóm tốn công lớn nhất là **box bị sót phải vẽ thêm** (`31` box × `1.0` = `31.0` điểm, chiếm **68,3%** tổng chi phí), nổi bật ở 3 nhóm vật thể:
    1. **Xe cỡ lớn (`Bus`/`Truck`)** mà model KITTI không có lớp hoặc không khớp kích thước: xe buýt đỏ 12 m ngay bên trái (`s02f02`), xe tải nhẹ/xe tải ben lớn (`s03f07`, `s04f19`, `s05f16`) và xe tải van Iveco (`s05f16`, `s05f46`).
    2. **Người đi bộ (`Pedestrian`) và người đi xe máy (`Cyclist`)** bị sót trên vỉa hè/làn xe máy hoặc ngay phía sau xe (`s02f22`, `s03f07`, `s04f03`, `s04f19`, `s04f44`).
    3. **Xe con ở xa (`25–40 m`) hoặc bị che khuất một phần** rơi xuống dưới ngưỡng `score_thr=0.5` (`s02f22`, `s02f55`, `s03f07`, `s03f46`, `s04f03`, `s04f19`, `s05f16`, `s05f46`).
  - Nhóm đứng thứ hai là **box thừa cần xóa** (`43` box × `0.3` = `12.9` điểm, chiếm 28,4%), chủ yếu nằm trên dải phân cách/bụi cây, hàng rào/trạm xe buýt, bia đá/tượng trang trí (`s03f25`, `s05f46`), xe hai bánh dựng không người và nhiễu xuyên qua thân xe buýt (`s02f02`).
  - Nhóm **box cần sửa** tính theo công thức chỉ có `3` box (`1.5` điểm — chủ yếu đổi lớp `Car -> Truck` và chỉnh chiều cao/kích thước như van chở hàng ở `s03f07`, xe tải thùng ở `s05f46`, MPV ở `s04f19`), nhưng khi kiểm tra thực tế trên CVAT vẫn cần xoay lại đầu xe bị ngược `180°` và hạ/nâng `z` sát mặt đường cho một số hộp (vốn không bị tính vào mục `sửa` vì công thức so góc modulo `180°`).

## 5. Giới hạn

- **Cỡ mẫu tune quá nhỏ (3 frame tập A):** 3 frame không đại diện đủ cho mọi mật độ giao thông và bối cảnh đường phố. Kết quả leave-one-out đã cho thấy cấu hình tốt nhất dao động giữa `0.3–0.5`, và khi áp `score_thr=0.5` sang 12 frame tập B, tỷ lệ chi phí do phải thêm vật bị sót chiếm tới 68,3%.
- **Lệch miền dữ liệu của model KITTI pre-trained:** PointPillars học trên bộ KITTI (LiDAR 64 tia, chỉ nhìn phía trước, chỉ có 3 lớp `Car`/`Cyclist`/`Pedestrian`) nên không có lớp `Truck`/`Bus`, hay bỏ sót `Pedestrian`/`Cyclist` và nhận nhầm bụi cây, hàng rào, xe đạp dựng không người trên dữ liệu VF 360°.
- **Công thức chi phí chưa phải thời gian sửa thật:** Trọng số `0.3·xóa + 1.0·thêm + 0.5·sửa` là thước đo quy ước trong phạm vi 50 m (và so yaw modulo `180°`, không cộng công chỉnh `z` hay quay đầu `180°`), nên không thể quy đổi mức giảm 30% trên tập A thành thời gian hay giờ công thực tế tiết kiệm được.
- **Công cụ hỗ trợ kiểm tra:** Trong quá trình đối chiếu và kiểm tra chất lượng 3D trên tập A và tập B, tôi có dùng thêm script nội bộ (không nằm trong pre-label gốc của lab) để phóng to từng hộp lên 7 ảnh camera, vẽ bản đồ BEV theo độ cao và kiểm tra hình học point cloud bằng `scripts/vf_qa.py` trước khi cập nhật và xuất nhãn `Shape` từ CVAT.

