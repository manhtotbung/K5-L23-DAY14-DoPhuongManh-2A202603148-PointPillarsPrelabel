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
| Gốc | | | | |
| `best_config.json` | | | | |

- Tham số đã đổi trong `best_config.json`: ...
- Kết quả leave-one-out (dán các dòng `scripts/pp_sweep.py` in ra): ...
- Cấu hình có ổn định trên từng frame không? Vì sao tôi vẫn chọn (hoặc không chọn) nó: ...

## 3. Trước/sau (bước 8)

![so sánh](../../d14_148/compare/<frame>.jpg)

- `scripts/pp_compare.py` báo giảm (hoặc tăng) ...% công sửa trên tập A.
- Dự đoán ở mục 1 đúng hay sai? Giải thích bằng số box xóa/thêm/sửa: ...

## 4. Tập B

Số đo từ `scripts/pp_prelabel.py --frames d14_148/frames_B.txt --config d14_148/best_config.json --gt d14_148/ref_B.json`:

| Xóa | Thêm | Sửa | Chi phí |
|---:|---:|---:|---:|
| | | | |

- Loại box tốn công sửa nhất ở tập B: ...

## 5. Giới hạn

- ...
