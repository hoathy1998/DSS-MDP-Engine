# Hệ thống quyết định hai pha theo Fig. 1

Tài liệu này mô tả cách dự án hiện thực kiến trúc ở Fig. 1 (tr. 2) của Voorberg et al. (2021). Bài báo chia cách tiếp cận thành hai pha tuần tự: pha thiết kế (design time) và pha triển khai (deployment).

## Chạy thử

```
conda activate dss-repro
python scripts/design_time.py --export-cmmn   # pha thiết kế, tạo gói trong results/deploy/koffer
python scripts/run_system.py                  # pha triển khai, mở http://127.0.0.1:8600
```

Sau lần đầu, bỏ `--export-cmmn` để `models/koffer.cmmn` là nguồn mô hình. Sửa tệp này rồi chạy lại `design_time.py` thì MDP đổi theo.

## Đối chiếu với Fig. 1

| Khối trong Fig. 1 | Mục | Hiện thực |
|---|---|---|
| Create CMMN model | 5.1 | `models/koffer.cmmn`, CMMN 1.1 XML |
| Retrieve MDP structure | 5.2 | `cmmn.retrieve_structure`: tác vụ, giai đoạn, thứ tự trước sau, mục bắt buộc |
| Create Information Structure | 5.3 | `data/koffer.yaml`: hàm Y, chi phí, phân phối |
| Filter MDP | 5.4 | `design.filter_model`, `DIPModel`; báo lỗi nếu CMMN và tham số không khớp |
| Solve MDP | 5.5 | `solve_array`; kết quả là gói triển khai có mã băm |
| CMMN User Model + Plan Fragment → CMMN Model | 6.1 | `cmmn.integrate_plan_fragment`, ghi ra `integrated.cmmn` |
| MDP Recommender | 6.2 | `recommender.MDPRecommender`: tra bảng, không giải lại |
| CMMN Engine | 6, 7.3 | `engine.CaseEngine`, nhật ký sự kiện SQLite |
| Task | 6 | Giao diện `TaskExecutor`; hiện dùng `SimulatedExecutor` |
| Decision Maker | 6.3 | `server.py`, `ui.html`: chọn hành động, có thể làm khác khuyến nghị |

Pha triển khai chỉ đọc gói, không đọc `data/`. Nếu gói bị sửa sau khi tạo, `load_package` từ chối mở.

## Vòng điều phối

Đúng theo mục 6: hỏi bộ khuyến nghị → người quyết định chọn → nếu chọn thu thập thông tin thì chạy tác vụ, nhận kết quả, cập nhật trạng thái rồi hỏi lại → nếu chọn quyết định cuối thì đóng hồ sơ. Engine nhận mọi hành động được phép, kể cả khác khuyến nghị, và luôn có khuyến nghị cho trạng thái mới.

## Màn hình người quyết định

Màn hình chia hai cột để xem hồ sơ và khuyến nghị cùng lúc. Cột trái là hồ sơ: chọn hồ sơ và hai sơ đồ. Cột phải luôn nằm trong tầm nhìn khi cuộn: chi tiết bước đang xét, giá trị kỳ vọng, tập hành động kèm lợi nhuận kỳ vọng, rồi đến quy định và sự kiện (có thể thu gọn). Màn hình hẹp hơn 1000 px thì hai cột xếp chồng.

Hai sơ đồ được dựng từ mô hình trong gói qua `/api/meta`; sửa CMMN rồi chạy lại pha thiết kế thì sơ đồ đổi theo.

- **Vòng điều phối**: bốn bước của mục 6 (hỏi bộ khuyến nghị → thông tin hay quyết định → chạy tác vụ → đóng hồ sơ). Bước hồ sơ đang ở được tô đậm và nhấp nháy.
- **Quy trình hồ sơ**: mọi mục của mô hình CMMN. Giai đoạn là khung nét đứt, mũi tên là thứ tự trước sau, vạch đậm bên trái đánh dấu mục bắt buộc. Màu cho biết trạng thái: khuyến nghị (đậm nhất, có dấu ★), được phép, đang chạy, đã xong (kèm giá trị thu được), chưa mở khóa, hoặc bỏ qua khi hồ sơ đã đóng (kèm giá trị thật). Ô "Quyết định báo giá" ghi số mục bắt buộc đã xong. Bấm vào một mục được phép để làm mục đó; rê chuột hoặc dùng phím Tab để xem chi phí, lợi nhuận kỳ vọng và lý do bị khóa.

Khung "Quy định quy trình" liệt kê các quy định rút từ mô hình: mục bắt buộc, mục tùy chọn, giai đoạn, thứ tự trước sau, mỗi tác vụ làm một lần. Nút "Tự chạy theo khuyến nghị" cho hồ sơ tự đi theo khuyến nghị đến khi đóng, để xem toàn bộ quy trình. Mỗi tác vụ mô phỏng mất `--task-seconds` (mặc định 1,5 giây).

**Làm khác khuyến nghị theo kinh nghiệm.** Khi người quyết định chọn hành động có lợi nhuận kỳ vọng thấp hơn khuyến nghị, màn hình hiện hộp xác nhận ghi mức thiệt kỳ vọng (Q của khuyến nghị trừ Q của hành động được chọn) và ô nhập lý do. Engine lưu `expected_loss` và `reason` vào sự kiện `action_selected`; khi hồ sơ đóng, cột phải liệt kê các lần làm khác và cộng các mức thiệt tại từng bước. Lựa chọn ngang giá trị (ví dụ thứ tự giữa các mục bắt buộc) không bị hỏi.

Quy định do engine kiểm tra chứ không chỉ do giao diện. Hành động vi phạm bị trả lỗi 409 kèm tên quy định, ví dụ `required tasks not done yet: beta, 3, 4, C, E`.

## "Thời gian thực" ở đây nghĩa là gì

Việc tính toán nặng đã xong ở pha thiết kế. Khi chạy, mỗi khuyến nghị chỉ là phép tra bảng, còn thay đổi của hồ sơ được đẩy tới màn hình qua server-sent events, người dùng không phải tải lại trang.

Số đo trong `results/system_latency.json` (`scripts/measure_system.py`): 200 hồ sơ, 8 luồng đồng thời, client và server cùng một máy, tác vụ hoàn thành tức thì.

| Đại lượng | Trung vị | p99 | Lớn nhất |
|---|---:|---:|---:|
| Tra khuyến nghị | 0,073 ms | 0,139 ms | 0,277 ms |
| Từ lúc gửi lựa chọn đến khi nhận khuyến nghị mới | 4,7 ms | 21,8 ms | 517 ms |
| Từ lúc gửi lựa chọn đến khi sự kiện được đẩy tới | 8,6 ms | 24,3 ms | 521 ms |

Đây là độ trễ của riêng hệ thống. Thời gian thật của một hồ sơ phụ thuộc vào các tác vụ, chẳng hạn chờ báo giá thị trường. Hệ thống không có cam kết thời gian cứng kiểu hard real-time. Chưa tìm hiểu nguyên nhân của các giá trị lớn nhất khoảng 0,5 giây; chúng chỉ xuất hiện rất hiếm trong lần đo này.

## Giới hạn

- **Engine chỉ thực thi một tập con của CMMN**, và không chạy mọi ngữ nghĩa trong tệp tích hợp: vòng điều phối được viết trong mã, engine chỉ kiểm tra tệp có plan fragment. Tệp CMMN chưa được kiểm tra bằng XSD chính thức và chưa thử nạp vào Flowable hay công cụ mô hình hóa nào.
- **Tác vụ là mô phỏng.** Để nối với hệ thống thật, viết một lớp theo `TaskExecutor`; engine không cần đổi.
- **Không có đăng nhập hay phân quyền.** Server chỉ nghe trên `127.0.0.1`; cần thêm xác thực trước khi mở ra mạng.
- **Một tiến trình, một tệp SQLite**, đủ cho demo chứ chưa phải cho vận hành quy mô lớn.
- **Chính sách cố định sau pha thiết kế.** Muốn đổi chi phí hay phân phối phải chạy lại pha thiết kế.
- **Y vẫn là `margin_all`**, nên giới hạn về con số trong `results/summary.md` vẫn áp dụng. Hệ thống hoàn chỉnh về kiến trúc không làm các con số này gần bài báo hơn.
