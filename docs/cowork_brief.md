# Tài liệu nguồn cho báo cáo: hệ hỗ trợ quyết định thu thập thông tin theo Voorberg et al. (2021)

## 0. Cách dùng tài liệu này

Tài liệu này là nguồn duy nhất để viết phần báo cáo về sản phẩm (ý tưởng, thiết kế, kết quả, hạn chế, hướng phát triển) của đồ án CS2208 Hệ hỗ trợ quyết định, UIT. Học viên: Châu Ngọc Hoa Thy. GVHD: Ton That Hoa An, Ph.D.

Quy tắc khi viết báo cáo từ tài liệu này:

1. **Chỉ dùng các con số có trong tài liệu.** Mọi số liệu ở đây do mã của dự án sinh ra; tệp nguồn ghi trong ngoặc. Không làm tròn khác đi, không suy ra số mới. Nếu thấy cần một con số không có ở đây, hãy ghi "[cần bổ sung]" thay vì ước lượng.
2. **Phân biệt ba thứ:** điều bài báo viết, điều dự án tái hiện được, và điều dự án làm thêm. Mục 1 là bài báo; mục 4 là tái hiện; mục 3, 5 là phần làm thêm.
3. **Không nói quá.** Đây là bản demo chạy trên máy cá nhân với tác vụ mô phỏng, không phải hệ thống đã triển khai cho doanh nghiệp. Lợi nhuận tái hiện lệch đáng kể so với bài; phải nói rõ điều này.
4. Văn phong học thuật tiếng Việt. Thuật ngữ gốc giữ nguyên tiếng Anh ở lần đầu: Markov Decision Process (MDP), Case Management Model and Notation (CMMN), decision-intensive process (DIP), backward induction (quy nạp ngược), design time (pha thiết kế), deployment (pha triển khai).
5. Trích dẫn bài báo gốc: S. Voorberg, R. Eshuis, W. van Jaarsveld, G.-J. van Houtum, "Decisions for information or information for decisions? Optimizing information gathering in decision-intensive processes," *Decision Support Systems*, vol. 151, art. 113632, 2021.

## 1. Bài toán của bài báo

Trong một quy trình ra quyết định, người làm phải chọn giữa hai việc: thu thập thêm thông tin (tốn chi phí) hay quyết định ngay với thông tin đang có. Bài báo gọi loại quy trình này là decision-intensive process. Ý tưởng của bài là:

- Mô hình hóa quy trình bằng CMMN: các tác vụ, giai đoạn (stage), mục bắt buộc, thứ tự trước sau.
- Chuyển mô hình CMMN thành một MDP. Trạng thái là tập tác vụ đã làm cùng các giá trị thông tin đã biết; hành động là làm một tác vụ được phép hoặc ra quyết định cuối; phần thưởng là trừ chi phí tác vụ, cộng lợi nhuận kỳ vọng khi quyết định.
- Giải MDP bằng quy nạp ngược để có chính sách tối ưu cho mọi trạng thái.
- Đưa chính sách vào một bộ khuyến nghị chạy cùng bộ máy CMMN. Bài vẽ kiến trúc này ở Fig. 1 gồm hai pha: pha thiết kế (tạo mô hình CMMN, rút cấu trúc MDP, tạo cấu trúc thông tin, lọc MDP, giải MDP) và pha triển khai (tích hợp plan fragment vào mô hình CMMN, bộ máy CMMN hỏi bộ khuyến nghị, người quyết định chọn).

Ví dụ áp dụng là bài toán Koffer: một công ty bảo trì linh kiện máy bay quyết định có báo giá hợp đồng sửa chữa hay không, và báo giá bao nhiêu (không báo giá, 1.800, 2.000, 2.200). Mô hình có 9 thuộc tính thông tin (A đến I), 5 mục kế hoạch không thu thập thông tin (giai đoạn α, β và tác vụ 2, 3, 4), 4 phương án. Bài so sánh với cây quyết định do người quản lý xây dựng (Fig. 8) và báo cáo lợi nhuận kỳ vọng 15.867,6 cho MDP so với 8.226,0 cho cây (Bảng 5).

## 2. Ý tưởng của đồ án

Đồ án có hai phần.

**Phần 1, tái hiện.** Dựng lại toàn bộ phương pháp từ số liệu trong bài (Bảng 2–4), giải MDP Koffer đầy đủ, so sánh với cây quyết định theo các chỉ số của Bảng 5 và chín trường hợp của Bảng 6, rồi mở rộng bằng các chính sách đối chứng và phân tích độ nhạy. Bài báo không công bố mã nguồn, nên việc tái hiện cũng là một phép kiểm tra khả năng tái hiện của bài.

**Phần 2, hệ thống hai pha theo Fig. 1.** Bài báo mô tả kiến trúc nhưng không cung cấp hệ thống chạy được. Đồ án hiện thực kiến trúc đó thành một bản demo chạy trên máy cá nhân: đầu vào là một tệp CMMN XML chuẩn, pha thiết kế giải MDP và xuất gói triển khai, pha triển khai là một máy chủ web điều phối nhiều hồ sơ cùng lúc, hỏi bộ khuyến nghị ở mỗi bước và đẩy thay đổi tới màn hình người quyết định theo thời gian thực.

Có thêm hai bản demo phụ: ứng dụng Streamlit (`app/streamlit_app.py`) và một trang web tự chứa chạy bộ giải bằng JavaScript (`web/koffer_demo.html`). Hai bản này không thuộc trọng tâm của báo cáo về hệ thống.

## 3. Mục tiêu thiết kế

### 3.1 Phần tái hiện

| Mục tiêu | Cách đạt | Kiểm tra |
|---|---|---|
| Bộ giải tổng quát, không hard-code Koffer | Mô hình dựng từ YAML; cùng mã giải ví dụ nhỏ và Koffer | `tests/test_toy.py`, `tests/test_model.py` |
| Giải chính xác 8.100.000 trạng thái | Mã hóa trạng thái hỗn hợp cơ số, quy nạp ngược trên mảng, biên dịch bằng numba | `tests/test_solver_array.py` (so với bản đệ quy) |
| Kết quả tự nhất quán | V(gốc) bằng lợi nhuận mô phỏng trên toàn bộ 16.384 kịch bản, sai số < 1e-6 | `tests/test_consistency.py` |
| Không bịa số, chạy lại được | Mọi số trong `results/` do script sinh ra; mọi lựa chọn khi bài mơ hồ có mã giả định A1–A15 | `docs/assumptions.md` |

### 3.2 Phần hệ thống hai pha

| Mục tiêu | Lựa chọn thiết kế |
|---|---|
| **Tách hai pha như Fig. 1** | Pha thiết kế xuất một gói (`integrated.cmmn`, `model.json`, `policy.npz`, `manifest.json`). Pha triển khai chỉ đọc gói, không đọc dữ liệu gốc |
| **Mô hình quy trình là nguồn sự thật** | Thứ tự trước sau và mục bắt buộc rút từ CMMN XML (`requiredRule`, `entryCriterion`/sentry, `stage`); chi phí và phân phối lấy từ tệp tham số. Hai nguồn không khớp thì báo lỗi |
| **An toàn khi đổi mô hình** | Gói có mã băm SHA-256 cho từng tệp; pha triển khai từ chối gói đã bị sửa |
| **Phản hồi tức thì** | Phần tính nặng làm xong ở pha thiết kế; khi chạy, mỗi khuyến nghị chỉ là một phép tra bảng |
| **Người quyết định giữ quyền** (mục 6.3 của bài) | Mọi hành động hợp lệ đều được nhận, kể cả khác khuyến nghị; hệ thống khuyến nghị tiếp từ trạng thái mới và ghi nhận "khác khuyến nghị" |
| **Kết hợp kinh nghiệm con người với mô hình** | Khi người quyết định chọn hành động kém hơn khuyến nghị, màn hình báo trước mức thiệt kỳ vọng (chênh lệch lợi nhuận kỳ vọng so với khuyến nghị) và mời ghi lý do, ví dụ kinh nghiệm hay thông tin ngoài mô hình. Lý do và mức thiệt được lưu vào nhật ký hồ sơ và tổng hợp khi đóng hồ sơ. Lựa chọn ngang giá trị khuyến nghị thì không bị hỏi |
| **Quy định quy trình do hệ thống kiểm soát** | Engine kiểm tra mục bắt buộc, thứ tự trước sau, giai đoạn, mỗi tác vụ làm một lần; hành động vi phạm bị từ chối kèm tên quy định |
| **Truy vết và phục hồi** | Mỗi hồ sơ là một chuỗi sự kiện ghi vào SQLite (event sourcing); khởi động lại thì hồ sơ đang mở tiếp tục |
| **Dễ thay tác vụ mô phỏng bằng hệ thống thật** | Tác vụ đi qua giao diện `TaskExecutor`; bản demo dùng `SimulatedExecutor` |
| **Không phụ thuộc thư viện ngoài cho phần chạy** | Máy chủ dùng thư viện chuẩn Python (`http.server`, server-sent events), giao diện là một tệp HTML |

### 3.3 Màn hình người quyết định

Màn hình chia hai cột để xem hồ sơ và khuyến nghị cùng lúc.

- Cột trái: sơ đồ vòng điều phối của Fig. 1 (hỏi bộ khuyến nghị → thông tin hay quyết định → chạy tác vụ → đóng hồ sơ), bước hiện tại được tô sáng; sơ đồ quy trình CMMN với mọi mục, giai đoạn là khung nét đứt, mũi tên là thứ tự trước sau, vạch đậm đánh dấu mục bắt buộc, màu cho biết trạng thái (khuyến nghị, được phép, đang chạy, đã xong, chưa mở khóa).
- Cột phải: chi tiết bước đang xét, chi phí đã bỏ ra, giá trị kỳ vọng, danh sách hành động được phép kèm lợi nhuận kỳ vọng của từng hành động, khung quy định quy trình và nhật ký sự kiện trực tiếp.
- Có chế độ "tự chạy theo khuyến nghị" để xem toàn bộ quy trình chạy đến khi đóng hồ sơ.
- Sơ đồ dựng từ mô hình trong gói, không vẽ cố định.

## 4. Kết quả tái hiện (nguồn: `results/summary.md`)

Cấu hình mặc định: hàm Y theo công thức in ở tr. 10 của bài, Y = E·B·H·P(D ≥ f)·[f − A(1 − 0,2G) − F − I] (biến thể `margin_all`, giả định A3). Biến thể đối chứng `margin_repair` trừ F và I một lần cho mỗi hợp đồng; biến thể này gần số của bài hơn nhưng không có căn cứ trong bài.

| Chỉ số | Bài báo | `margin_all` | `margin_repair` |
|---|---:|---:|---:|
| MDP: lợi nhuận kỳ vọng | 15.867,60 | 8.762,62 (−44,8%) | 17.506,47 (+10,3%) |
| MDP: chi phí trung bình | 143,50 | 123,52 | 132,47 |
| MDP: số trạng thái kết thúc | 136 | 196 | 50 |
| Cây: lợi nhuận kỳ vọng | 8.226,00 | 3.643,66 (−55,7%) | 10.385,86 (+26,3%) |
| Cây: chi phí trung bình | 100,06 | 100,06 | 100,06 |
| Cây: số trạng thái kết thúc | 1.254 | 1.254 | 1.254 |

Nhận định chính:

- **Phương pháp tái hiện được và tự nhất quán**: V(gốc) bằng lợi nhuận mô phỏng trên 16.384 kịch bản.
- **Xu hướng của Bảng 5 tái hiện được** ở cả hai biến thể Y: MDP lợi nhuận cao hơn, ít trạng thái kết thúc hơn, chi phí thu thập cao hơn cây.
- **Con số tuyệt đối không tái hiện được.** Cây quyết định khớp đúng chi phí 100,06 và 1.254 trạng thái kết thúc, nên cấu trúc và phân phối được xác nhận; chênh lệch nằm ở hàm Y mà tác giả thực sự dùng. Trong 108 cách đặt số hạng chi phí vào Y, không cách nào khớp cả hai con số lợi nhuận trong phạm vi 5%.
- **Bảng 6 tự mâu thuẫn**: cây kiểm tra E đầu tiên nên lợi nhuận −45 chỉ có thể xảy ra khi E = 0, nhưng các trường hợp có cùng giá trị E lại cho kết quả trái ngược. Chỉ 3/9 trường hợp khớp.
- **Ví dụ nhỏ ở mục 5.3 của bài tính sai**: giá trị đúng là V = 1,0 (quyết định ngay), bài ghi 0,5.
- **Mức lợi của MDP phụ thuộc mốc so sánh**: chính sách "chỉ làm tác vụ bắt buộc rồi quyết định" đạt 5.733,87, đã cao hơn cây (3.643,66); chính sách tham lam một bước đạt 8.726,65, bằng 99,6% MDP.
- **Chính sách bền với sai số ước lượng**: với nhiễu ±10% và ±20% trên chi phí và phân phối, mức thiệt do giữ chính sách cũ thay vì giải lại lớn nhất là 0,05 (0,001%).
- **Quy mô**: 8.100.000 trạng thái, 640.224 đi tới được; giải trong 0,91 giây (`results/runtime.json`). Bài ghi 49 phút trên máy khác, nên hai con số không so sánh trực tiếp được.

## 5. Kết quả của hệ thống hai pha

- Pha thiết kế giải và đóng gói trong 0,878 giây (`results/deploy/koffer/manifest.json`); V(gốc) = 8.762,62, khớp kết quả tái hiện.
- Độ trễ đo qua HTTP thật, 200 hồ sơ, 8 luồng đồng thời, client và server cùng một máy, tác vụ hoàn thành tức thì (`results/system_latency.json`):

| Đại lượng | Trung vị | p99 | Lớn nhất |
|---|---:|---:|---:|
| Tra khuyến nghị | 0,073 ms | 0,139 ms | 0,277 ms |
| Từ lúc gửi lựa chọn đến khi nhận khuyến nghị mới | 4,7 ms | 21,8 ms | 517 ms |
| Từ lúc gửi lựa chọn đến khi màn hình được đẩy sự kiện | 8,6 ms | 24,3 ms | 521 ms |

  Giá trị lớn nhất khoảng 0,5 giây rất hiếm và chưa được tìm hiểu nguyên nhân.
- Kiểm thử: toàn bộ dự án 133 kiểm thử đạt; riêng hệ thống hai pha 27 kiểm thử, gồm: CMMN và tham số khớp nhau, gói bị sửa thì bị từ chối, hồ sơ chạy hết vòng, làm khác khuyến nghị vẫn được khuyến nghị tiếp, lý do và mức thiệt kỳ vọng của mỗi lần làm khác được ghi đúng, hành động sai quy định bị từ chối kèm tên quy định, khởi động lại thì phục hồi hồ sơ, luồng sự kiện trực tiếp đúng thứ tự và không lộ kịch bản ẩn.

## 6. Hạn chế của bản demo

**Về mô hình (kế thừa từ bài báo)**
- Các thuộc tính được giả định độc lập. Khi cho D phụ thuộc A, dự án chỉ đánh giá lại chính sách cũ chứ không giải lại.
- Thông tin thu được là chính xác tuyệt đối, không có sai số đo.
- Mỗi lần chỉ làm một tác vụ, và mô hình không tính thời gian chờ hay hạn chót; doanh nghiệp thật thường làm song song và có hạn nộp báo giá.
- Hàm Y không khớp số của bài, nên giá trị tuyệt đối của lợi nhuận chỉ có ý nghĩa trong mô hình này.
- Số trạng thái tăng theo hàm mũ với số thuộc tính và số giá trị; cách giải chính xác chỉ phù hợp với mô hình cỡ Koffer.

**Về hệ thống**
- Engine là bản tự viết cho một tập con CMMN, không phải Camunda hay Flowable, vì kế hoạch loại bộ máy CMMN thật khỏi phạm vi (giả định A15). Vòng điều phối được viết trong mã; engine chỉ kiểm tra tệp tích hợp có plan fragment.
- Tệp CMMN chưa được kiểm tra bằng XSD chính thức và chưa được nạp thử vào công cụ CMMN nào.
- Tác vụ là mô phỏng: kết quả lấy từ một kịch bản ẩn được rút từ chính phân phối của mô hình, nên mô hình luôn "đúng" với dữ liệu, điều không có ngoài thực tế.
- Không có đăng nhập, phân quyền hay mã hóa đường truyền; máy chủ chỉ nghe trên 127.0.0.1.
- Một tiến trình, một tệp SQLite; chưa thử tải trên mạng thật hay nhiều máy.
- Chính sách cố định sau pha thiết kế; đổi chi phí hay phân phối phải chạy lại pha thiết kế, và hồ sơ đang mở không được chuyển sang chính sách mới.
- Độ trễ đo trên cùng một máy, nên chưa tính độ trễ mạng.
- Giao diện mới được kiểm tra bằng ảnh chụp màn hình trên desktop; chưa kiểm tra chế độ tối, điện thoại, và chưa có người dùng thật thử.
- Dữ liệu duy nhất là ví dụ Koffer trong bài; không có dữ liệu doanh nghiệp thật.

## 7. Cần làm thêm để thành ứng dụng thực tiễn

Xếp theo thứ tự nên làm.

1. **Dữ liệu thật để ước lượng mô hình.** Ước lượng phân phối của từng thuộc tính và chi phí từng tác vụ từ lịch sử hồ sơ (nhật ký sự kiện của chính hệ thống là nguồn tự nhiên). Xác định hàm lợi nhuận Y cùng bộ phận kinh doanh và kiểm chứng trên các hợp đồng đã làm, vì đây là điểm dự án không tái hiện được từ bài.
2. **Theo dõi và cập nhật chính sách.** So sánh định kỳ phân phối thực tế với phân phối của mô hình; giải lại khi lệch, có phiên bản chính sách, và quy tắc cho hồ sơ đang mở khi đổi phiên bản. Phân tích độ nhạy cho thấy chính sách khá bền với nhiễu ±20%, nên tần suất cập nhật có thể thấp.
3. **Tích hợp hệ thống tác vụ.** Viết các lớp `TaskExecutor` nối tới hệ thống thật (ERP, CRM, email gửi bộ phận kỹ thuật, biểu mẫu nhập liệu cho tác vụ thủ công), xử lý tác vụ kéo dài nhiều ngày, thất bại và làm lại.
4. **Dùng bộ máy CMMN chuẩn.** Chạy mô hình trên Camunda hoặc Flowable và đưa bộ khuyến nghị thành dịch vụ riêng được gọi từ plan fragment, đúng như Fig. 1; kiểm tra tệp CMMN bằng XSD chính thức.
5. **An toàn và vận hành.** Đăng nhập, phân quyền theo vai trò (người quyết định, người thực hiện tác vụ, quản trị), HTTPS, nhật ký kiểm toán, sao lưu; chuyển SQLite sang cơ sở dữ liệu máy chủ (ví dụ PostgreSQL) và chạy nhiều tiến trình.
6. **Mở rộng mô hình cho sát thực tế.** Thuộc tính phụ thuộc nhau, thông tin có sai số, tác vụ song song, hạn chót. Các mở rộng này làm không gian trạng thái lớn hơn nhiều, nên cần phương pháp xấp xỉ (approximate dynamic programming, học tăng cường); chính sách tham lam một bước đạt 99,6% MDP trên Koffer là một gợi ý cho hướng xấp xỉ rẻ.
7. **Giải thích và đánh giá với người dùng.** Hiển thị vì sao một hành động được khuyến nghị (giá trị thông tin, rủi ro), thử nghiệm với người quyết định thật, đo mức chấp nhận khuyến nghị và lợi nhuận thực tế so với cách làm cũ.

## 8. Giả định quan trọng cần nhắc trong báo cáo (nguồn: `docs/assumptions.md`)

| Mã | Nội dung ngắn |
|---|---|
| A1 | B ~ Binomial(n = 3, p = 0,2) trên {40, 60, 80, 100}; được xác nhận vì khớp chi phí và số trạng thái của cây |
| A2 | Với Bernoulli(p), p ứng với giá trị thứ hai |
| A3 | Y theo công thức in (`margin_all`), đối chứng `margin_repair`; không biến thể nào khớp Bảng 5 |
| A5 | Cây đọc theo Fig. 8; Bảng 6 tự mâu thuẫn nên không dùng để hiệu chỉnh |
| A8 | Ví dụ nhỏ dùng giá trị đúng V = 1,0 |
| A9, A10 | Quy tắc hòa: ưu tiên quyết định, rồi chi phí thấp hơn, rồi thứ tự trong tệp; dung sai 1e-9 |
| A15 | Pha triển khai dùng engine Python tự viết cho tập con CMMN thay vì Camunda/Flowable |

## 9. Kiến trúc mã nguồn (để mô tả trong báo cáo)

| Thành phần | Tệp | Vai trò |
|---|---|---|
| Dữ liệu | `data/koffer.yaml`, `data/decision_tree.yaml`, `data/paper_results.yaml` | Bảng 2–4, Fig. 8, Bảng 5–6 chép từ bài |
| Mô hình MDP | `src/dipmdp/model.py` | Trạng thái, hành động được phép, phần thưởng, chuyển trạng thái |
| Cấu trúc thông tin | `src/dipmdp/information_structure.py` | Hàm Y và E[Y] |
| Bộ giải | `src/dipmdp/solver.py` | Bản đệ quy (tham chiếu) và bản mảng numba |
| Chính sách và đánh giá | `src/dipmdp/policies.py`, `evaluate.py`, `decision_tree.py`, `sensitivity.py` | MDP, cây, ba chính sách đối chứng; đánh giá trên 16.384 kịch bản |
| CMMN | `models/koffer.cmmn`, `src/dipmdp/system/cmmn.py` | Mô hình CMMN XML; rút cấu trúc; tích hợp plan fragment |
| Pha thiết kế | `src/dipmdp/system/design.py`, `scripts/design_time.py` | Lọc mô hình, giải, xuất gói có mã băm |
| Bộ khuyến nghị | `src/dipmdp/system/recommender.py` | Tra chính sách, trả hành động tốt nhất và giá trị mọi hành động |
| Engine | `src/dipmdp/system/engine.py` | Vòng điều phối, kiểm tra quy định, nhật ký sự kiện, phục hồi |
| Máy chủ và giao diện | `src/dipmdp/system/server.py`, `ui.html` | API JSON, server-sent events, màn hình người quyết định |
| Chạy demo | `scripts/run_system.py`, `scripts/demo.py` | Khởi động pha triển khai |

## 10. Gợi ý bố cục phần báo cáo về sản phẩm

1. Ý tưởng và bối cảnh (mục 1, 2)
2. Mục tiêu thiết kế (mục 3)
3. Kiến trúc hai pha và đối chiếu Fig. 1 (mục 3.2, 9; xem thêm `docs/system.md`)
4. Kết quả tái hiện và kết quả hệ thống (mục 4, 5)
5. Hạn chế (mục 6)
6. Hướng phát triển thành ứng dụng thực tiễn (mục 7)
7. Kết luận: phương pháp tái hiện được, xu hướng đúng, con số tuyệt đối không tái hiện được do bài thiếu thông tin về hàm Y; kiến trúc Fig. 1 hiện thực được ở mức demo với phản hồi dưới một mili giây cho mỗi khuyến nghị.

Hình có thể dùng: `results/fig_decisions.png`, `results/fig_task_usage.png`, `results/fig_tornado.png`, `docs/fig8_decision_tree.png`, và ảnh chụp màn hình bàn điều phối (cần chụp khi quay video).
