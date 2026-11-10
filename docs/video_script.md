# Kịch bản video trình bày: hệ hỗ trợ quyết định hai pha theo Voorberg et al. (2021)

**Thời lượng mục tiêu: khoảng 9 phút** (giới hạn dưới 10 phút).

| Phần | Nội dung | Thời lượng | Mốc kết thúc |
|---|---|---:|---:|
| 0 | Mở đầu | 0:30 | 0:30 |
| 1 | Giải thích mã nguồn | 3:40 | 4:10 |
| 2 | Demo trên localhost | 4:25 | 8:35 |
| 3 | Kết luận | 0:40 | 9:15 |

Mỗi đoạn có ba dòng: **Màn hình** (mở gì), **Thao tác** (làm gì), **Lời thoại** (nói gì). Lời thoại là gợi ý, nói lại theo cách tự nhiên của mình. Nếu đoạn nào vượt thời gian thì bỏ bớt câu trong ngoặc vuông [ ] trước. Các con số trong lời thoại đã được kiểm tra với kết quả của mã, ứng với hồ sơ seed 42 mà màn hình tự mở.

## Chuẩn bị trước khi quay

1. Mở PowerShell tại thư mục dự án và đặt đường dẫn Python (máy này không có lệnh `conda` trong PowerShell):
   ```
   cd C:\Doris\uit-master\HK3.CS2208-DSS\voorberg-mdp-repro
   $py = "C:\Users\dorislearndata\.conda\envs\dss-repro\python.exe"
   ```
2. Chạy kiểm thử một lần **trước khi quay**, để kết quả còn trên terminal khi nhắc tới: `& $py -m pytest -q` (khoảng 70 giây, phải ra `133 passed`).
3. Tắt mọi server đang chạy trên cổng 8600 (cửa sổ `run_system.py` hoặc `demo.py` cũ: Ctrl+C).
4. Mở sẵn các tab VS Code theo thứ tự quay: `README.md`, `data/koffer.yaml`, `src/dipmdp/model.py`, `src/dipmdp/solver.py`, `results/summary.md`, `models/koffer.cmmn`, `src/dipmdp/system/design.py`, `src/dipmdp/system/engine.py`.
5. Phóng to chữ VS Code (Ctrl+=) và trình duyệt (Ctrl+= hai lần). Màn hình nên rộng ít nhất 1280 px để bàn điều phối hiện hai cột.
6. Mở sẵn ảnh Fig. 1 của bài báo (`../Paper/`) và một terminal thứ hai cũng đã đặt `$py`.
7. Tập một lần với đồng hồ bấm giờ.

## Phần 0. Mở đầu (0:30)

**Màn hình:** Fig. 1 của bài báo.

**Lời thoại:**
> Em xin trình bày đồ án tái hiện bài báo của Voorberg và cộng sự năm 2021. Câu hỏi của bài là: trong một quy trình ra quyết định, lúc nào nên thu thập thêm thông tin, lúc nào nên quyết định ngay. Bài mô hình hóa quy trình bằng CMMN, chuyển thành quá trình quyết định Markov, giải bằng quy nạp ngược, rồi đưa vào bộ khuyến nghị theo kiến trúc hai pha ở hình này. Bài không công bố mã. Em tái hiện phương pháp, rồi hiện thực kiến trúc này thành hệ thống chạy được.

## Phần 1. Giải thích mã nguồn (3:40)

### 1.1 Cấu trúc và dữ liệu (0:40)

**Màn hình:** `README.md` mục "Cấu trúc", rồi `data/koffer.yaml`.

**Thao tác:** Ở `koffer.yaml`, chỉ vào `required`, `preceding` của một mục, rồi `information_structure.variants`.

**Lời thoại:**
> Dự án viết bằng Python. `data` chứa số liệu chép từ bài, `src/dipmdp` là mã nguồn, trong đó thư mục `system` là hệ thống hai pha; `results` là kết quả do mã sinh ra. Đây là bài toán Koffer: công ty bảo trì linh kiện máy bay quyết định có báo giá hợp đồng không và bao nhiêu. Có 9 thuộc tính thông tin, mỗi thuộc tính có tác vụ thu thập với chi phí và phân phối riêng. `required` là mục bắt buộc, `preceding` là thứ tự trước sau. Cuối tệp là hàm lợi nhuận Y, em dùng đúng công thức in trong bài.

### 1.2 Mô hình và bộ giải (0:50)

**Màn hình:** `src/dipmdp/model.py`, hàm `allowed_actions` (dòng 124), rồi `src/dipmdp/solver.py`, hàm `solve_array` (dòng 268).

**Lời thoại:**
> Lớp `DIPModel` dựng MDP từ tệp này. Trạng thái gồm các mục đã làm và giá trị đã biết của 9 thuộc tính, tổng cộng 8.100.000 trạng thái, đúng như bài. Hàm này cài hai quy tắc: tác vụ chỉ làm được khi các mục đứng trước đã xong, và chỉ được quyết định khi đủ mục bắt buộc. Bộ giải duyệt trạng thái theo số mục đã làm giảm dần, phần lặp biên dịch bằng numba, giải toàn bộ trong khoảng một giây. [Bản đệ quy `solve_recursive` dùng để kiểm tra, hai bản cho cùng kết quả.]

### 1.3 Kết quả tái hiện (0:45)

**Màn hình:** `results/summary.md`, mục 1 và bảng mục 3.

**Lời thoại:**
> Phương pháp tái hiện được: giá trị của MDP bằng đúng lợi nhuận mô phỏng trên toàn bộ 16.384 kịch bản, và xu hướng của Bảng 5 đúng, MDP lãi hơn cây quyết định. Nhưng con số không khớp: lợi nhuận MDP là 8.762,62, bài ghi 15.867,6. Cây quyết định khớp đúng chi phí 100,06 và 1.254 trạng thái kết thúc, nên cấu trúc mô hình đúng; chênh lệch nằm ở hàm lợi nhuận mà bài không công bố đủ. Em ghi lại chênh lệch chứ không chỉnh mô hình cho khớp.

### 1.4 Hệ thống hai pha (1:25)

**Màn hình:** `models/koffer.cmmn` (chỉ `requiredRule` của `PI_beta`), rồi `src/dipmdp/system/design.py` hàm `compile_package` (dòng 49), rồi `src/dipmdp/system/engine.py` hàm `select_action` (dòng 237).

**Lời thoại:**
> Hệ thống nhận đầu vào là tệp CMMN XML chuẩn: mục bắt buộc đánh dấu bằng `requiredRule`, thứ tự là các sentry, alpha và beta là stage.
>
> Pha thiết kế là hàm `compile_package`, đi đúng các khối của Fig. 1: rút cấu trúc từ CMMN, ghép chi phí và phân phối, lọc, giải MDP, tích hợp plan fragment của bộ khuyến nghị. Đầu ra là một gói có mã băm từng tệp; gói bị sửa thì pha triển khai từ chối mở.
>
> Pha triển khai là engine. Mỗi hồ sơ chạy vòng lặp: hỏi bộ khuyến nghị, chờ người quyết định chọn, chạy tác vụ, nhận kết quả, hỏi lại, đến khi quyết định. Bộ khuyến nghị chỉ tra bảng nên mỗi lần mất khoảng 0,07 mili giây. Người quyết định được chọn khác khuyến nghị, nhưng hành động sai quy định thì bị từ chối kèm lý do. Mọi thay đổi ghi thành sự kiện trong SQLite nên khởi động lại không mất hồ sơ. [Tác vụ đi qua giao diện `TaskExecutor`; bản demo dùng tác vụ mô phỏng.]
>
> Toàn dự án có 133 kiểm thử, tất cả đều đạt.

(Nếu còn thời gian, chuyển sang terminal có kết quả `133 passed` đã chạy trước.)

## Phần 2. Demo trên localhost (4:25)

### 2.1 Chạy hai pha (0:35)

**Thao tác:**
```
& $py scripts/design_time.py
& $py scripts/demo.py --task-seconds 1
```
Trình duyệt tự mở http://127.0.0.1:8600; nếu không, gõ địa chỉ này.

**Lời thoại:**
> Lệnh thứ nhất là pha thiết kế: giải 8.100.000 trạng thái trong chưa tới một giây và ghi gói. Lệnh thứ hai là pha triển khai: kiểm tra mã băm của gói, rồi mở máy chủ trên localhost cổng 8600. Mỗi tác vụ mô phỏng mất 1 giây.

### 2.2 Giới thiệu màn hình (0:40)

**Màn hình:** Bàn điều phối, hồ sơ seed 42 tự mở.

**Thao tác:** Chỉ lần lượt hai sơ đồ và cột phải. Rê chuột lên ô `F. PMA/DER` (đang khóa).

**Lời thoại:**
> Bên trái là hồ sơ. Sơ đồ trên là vòng điều phối của Fig. 1, ô sáng là bước đang ở: chờ người quyết định. Sơ đồ dưới là mô hình CMMN: khung nét đứt là giai đoạn, mũi tên là thứ tự, vạch đen là mục bắt buộc, ngôi sao là bước được khuyến nghị, ổ khóa là chưa được làm. Rê chuột vào PMA/DER thấy phải xong alpha và A trước. Bên phải là giá trị kỳ vọng và mọi hành động được phép kèm lợi nhuận kỳ vọng.

### 2.3 Đi theo khuyến nghị (1:10)

**Thao tác:** Bấm hành động được khuyến nghị ở cột phải ở mỗi bước. Với seed 42 các bước là: β → C → E → 3 → α → A → G → 2 → 4 → D. **Dừng lại khi khuyến nghị là "Báo giá 2000"**, sang đoạn 2.4. Nói trong lúc chờ tác vụ chạy.

**Lời thoại:**
> Ở bước đầu, năm mục bắt buộc cùng giá trị 8.762,6, vì đằng nào cũng phải làm hết; khi hòa, hệ thống chọn mục rẻ nhất, nên beta được khuyến nghị.
>
> Khi tác vụ chạy, ô chuyển màu cam, vòng điều phối sáng ở bước 3; kết quả về thì màn hình tự cập nhật, không cần tải lại.
>
> (Sau E) Năng lực nội bộ E bằng 1, công ty tự sửa được, giá trị kỳ vọng nhảy từ khoảng 8.764 lên 14.639.
>
> (Sau A) Chi phí sửa A bằng 1.900, khá cao, kỳ vọng giảm còn khoảng 8.821.
>
> (Sau G) G bằng 1 giảm 20% chi phí sửa, kỳ vọng lên khoảng 16.053, nên đáng bỏ tiền xin phép thị trường và ước tính giá thị trường D.
>
> (Khi khuyến nghị là báo giá 2.000) Biết D rồi, bộ khuyến nghị cho rằng nên báo giá 2.000 ngay, vì thông tin còn lại không đáng với chi phí.

### 2.4 Người quyết định làm khác khuyến nghị theo kinh nghiệm (0:50)

**Thao tác:**
1. Bấm "Chốt thời hạn hợp đồng" ở cột phải (không phải khuyến nghị). Hộp xác nhận màu cam hiện ra.
2. Bấm gợi ý "Kinh nghiệm với khách hàng này", hoặc gõ: *Kinh nghiệm: hợp đồng ngắn hạn thường lỗ, luôn chốt thời hạn trước khi báo giá*.
3. Bấm "Vẫn chọn". Chờ tác vụ xong (H = 1), rồi bấm khuyến nghị "Báo giá 2000".

**Lời thoại:**
> Đến đây, giả sử người quản lý có kinh nghiệm: hợp đồng ngắn hạn thường lỗ, nên luôn chốt thời hạn trước khi báo giá. Mô hình không biết kinh nghiệm này. Khi em chọn khác khuyến nghị, hệ thống không chặn mà báo trước cái giá phải trả: lợi nhuận kỳ vọng thấp hơn 4,0, đúng bằng chi phí của tác vụ. Em ghi lý do rồi xác nhận. Lý do được lưu vào nhật ký hồ sơ để sau này đối chiếu.
>
> Kết quả H bằng 1 năm. Bộ khuyến nghị tính lại từ trạng thái mới và vẫn đề nghị báo giá 2.000. Tức là bước kiểm tra theo kinh nghiệm này tốn 4 nhưng không đổi quyết định. Hệ thống giúp lượng hóa giá của một thói quen, còn quyền quyết định vẫn thuộc về con người, đúng tinh thần mục 6.3 của bài.

### 2.5 Kết quả khi đóng hồ sơ và chế độ tự chạy (0:30)

**Thao tác:** Chỉ vào ba con số và mục "Các lần làm khác khuyến nghị" ở cột phải. Sau đó bấm "Mở hồ sơ mới", bấm "Tự chạy theo khuyến nghị" và để chạy trong lúc nói.

**Lời thoại:**
> Hồ sơ đóng với giá 2.000, chi phí 214. Các ô mờ ghi "thật" là thông tin không mua, giờ mới tiết lộ: số lần sửa B thật chỉ là 40, nên lợi nhuận thật là 3.241,6. Bên dưới là tổng hợp: một lần làm khác khuyến nghị, thiệt kỳ vọng 4,0, kèm lý do. Với hồ sơ mới, nút tự chạy cho hồ sơ đi theo khuyến nghị đến hết, ô sáng di chuyển qua từng bước.

### 2.6 Quy định do máy chủ kiểm soát (0:20)

**Thao tác:** Ở terminal thứ hai (server vẫn chạy):
```
& $py scripts/demo_rule_check.py
```

**Lời thoại:**
> Quy định không chỉ nằm ở giao diện. Script này gọi thẳng API và cố tình vi phạm ba quy định: báo giá khi chưa đủ mục bắt buộc, làm F trước alpha và A, làm D trước tác vụ 2. Cả ba bị máy chủ từ chối, kèm tên quy định bị vi phạm.

## Phần 3. Kết luận (0:40)

**Màn hình:** Bàn điều phối hoặc slide kết luận.

**Lời thoại:**
> Tóm lại, đồ án tái hiện được phương pháp và xu hướng của bài, nhưng không tái hiện được con số lợi nhuận vì bài thiếu thông tin về hàm lợi nhuận; mọi giả định được ghi từ A1 đến A15. Kiến trúc hai pha được hiện thực thành hệ thống chạy được, mỗi khuyến nghị dưới một mili giây. Đây vẫn là bản demo: tác vụ mô phỏng, engine tự viết cho một phần CMMN, chưa có đăng nhập, dữ liệu chỉ là ví dụ trong bài. Để dùng thật cần dữ liệu doanh nghiệp, nối tác vụ với hệ thống thật, dùng bộ máy CMMN chuẩn và bổ sung bảo mật. Em cảm ơn thầy đã theo dõi.

## Phụ lục A: các lệnh

```
cd C:\Doris\uit-master\HK3.CS2208-DSS\voorberg-mdp-repro
$py = "C:\Users\dorislearndata\.conda\envs\dss-repro\python.exe"

& $py -m pytest -q                           # trước khi quay: 133 kiểm thử
& $py scripts/design_time.py                 # 2.1: pha thiết kế
& $py scripts/demo.py --task-seconds 1       # 2.1: pha triển khai, tự mở trình duyệt
& $py scripts/demo_rule_check.py             # 2.6: chạy ở terminal thứ hai
```

## Phụ lục B: đoạn tùy chọn nếu còn thời gian (khoảng 30 giây)

Phục hồi sau khi tắt máy chủ: trong terminal của server nhấn Ctrl+C, chạy `& $py scripts/demo.py --keep --task-seconds 1`, rồi chọn lại hồ sơ cũ trong ô "Đang xem".

> Em tắt máy chủ rồi bật lại với tùy chọn giữ dữ liệu. Các hồ sơ được phục hồi từ nhật ký sự kiện; hồ sơ đang dở tiếp tục từ đúng bước đã dừng.

## Phụ lục C: xử lý sự cố khi quay

| Hiện tượng | Cách xử lý |
|---|---|
| Trình duyệt báo `ERR_CONNECTION_REFUSED` | Server chưa chạy hoặc đã bị tắt; chạy lại `scripts/demo.py` và để nguyên cửa sổ đó |
| Báo cổng 8600 đang dùng | Một server cũ còn chạy; tắt nó, hoặc dùng `--port 8601` cho `demo.py` và `--base http://127.0.0.1:8601` cho `demo_rule_check.py` |
| `ModuleNotFoundError: dipmdp` | Chạy `& $py scripts/install_editable.py` một lần |
| Hồ sơ đầu tiên không phải seed 42 | Chưa xóa dữ liệu cũ; chạy `demo.py` không có `--keep` |
