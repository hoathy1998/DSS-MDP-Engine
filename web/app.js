// State and views of the web demo. createApp has no DOM access, so tests can drive it in Node:
// dispatch(message) changes the state and html() returns the markup for the current state.

const LABELS = {
  attributes: {
    A: "Chi phí sửa chữa ròng",
    B: "Số lần sửa mỗi năm",
    C: "Độ tin cậy khách hàng",
    D: "Giá thị trường trung bình",
    E: "Năng lực nội bộ",
    F: "Khả năng PMA/DER",
    G: "Hạng mục phát sinh",
    H: "Thời hạn hợp đồng (năm)",
    I: "Chi phí vận chuyển",
  },
  tasks: {
    alpha: "Mở giai đoạn: xác định tổng chi phí sửa chữa",
    beta: "Mở giai đoạn: xác định số lần sửa",
    2: "Xin phép cơ quan quản lý thị trường",
    3: "Thu thập thông tin hợp đồng",
    4: "Thu thập thông tin khách hàng",
    A: "Lấy chi phí sửa chữa ròng",
    B: "Ước tính số lần sửa mỗi năm",
    C: "Kiểm tra độ tin cậy khách hàng",
    D: "Ước tính giá thị trường",
    E: "Kiểm tra năng lực nội bộ",
    F: "Xác định khả năng PMA/DER",
    G: "Xác định hạng mục phát sinh",
    H: "Chốt thời hạn hợp đồng",
    I: "Lấy chi phí vận chuyển",
  },
  plan: { alpha: "α", beta: "β" },
};
const VARIANT_LABELS = {
  margin_all: "Công thức in trong bài",
  margin_repair: "Đối chứng: F, I tính một lần",
};
const VIEWS = [
  ["koffer", "Hồ sơ Koffer"],
  ["toy", "Ví dụ nhỏ"],
  ["about", "Về mô hình"],
];
const SAMPLE_SEED = 42;

function number(value, digits = 1) {
  const text = value.toLocaleString("vi-VN", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  return text.replace("-", "−");
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
}

function seededRandom(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function drawCase(attributes, random) {
  const values = {};
  for (const attr of attributes) {
    let u = random();
    let index = attr.probs.findIndex((p) => (u -= p) < 0);
    if (index < 0) index = attr.values.length - 1;
    values[attr.id] = attr.values[index];
  }
  return values;
}

function createApp(data, Y_FUNCTIONS, buildSolver, random = Math.random) {
  const solvers = new Map();

  function solverFor(model, variant) {
    const key = `${model}/${variant}`;
    if (!solvers.has(key)) {
      solvers.set(key, buildSolver(data[model], variant, Y_FUNCTIONS[model][variant]));
    }
    return solvers.get(key);
  }

  const state = {
    view: "koffer",
    variant: data.koffer.default_variant,
    caseId: "sample",
    toy: {},
    run: null,
  };

  function solver() {
    return solverFor("koffer", state.variant);
  }

  function startCase(trueValues, caseId) {
    state.caseId = caseId;
    state.run = { truth: trueValues, state: solver().rootState(), cost: 0, log: [], decision: null };
  }

  function caseValues(caseId) {
    if (caseId === "sample") return drawCase(data.koffer.attributes, seededRandom(SAMPLE_SEED));
    const row = data.table6.find((item) => String(item.instance) === caseId);
    return Object.fromEntries(data.koffer.attributes.map((attr, i) => [attr.id, row.final_state[i]]));
  }

  startCase(caseValues("sample"), "sample");

  function dispatch(message) {
    const [kind, argument] = message;
    if (kind === "view") state.view = argument;
    if (kind === "variant") {
      state.variant = argument;
      startCase(state.run.truth, state.caseId);
    }
    if (kind === "case") startCase(caseValues(argument), argument);
    if (kind === "random") startCase(drawCase(data.koffer.attributes, random), "random");
    if (kind === "restart") startCase(state.run.truth, state.caseId);
    if (kind === "toy") {
      const [id, value] = argument.split("=");
      if (value === "") delete state.toy[id];
      else state.toy[id] = Number(value);
    }
    if (kind === "do") act({ kind: "do", id: argument });
    if (kind === "decide") {
      act({ kind: "decide", decision: data.koffer.decisions.find((d) => String(d) === argument) });
    }
  }

  function act(action) {
    const run = state.run;
    const s = solver();
    const best = s.recommended(run.state);
    const same = best.kind === action.kind && best.id === action.id && best.decision === action.decision;
    run.log.push({ action: actionName(action), followed: same, recommended: actionName(best) });
    if (action.kind === "decide") {
      run.decision = action.decision;
      return;
    }
    run.cost += s.tasks.find((task) => task.id === action.id).cost;
    run.state = s.perform(run.state, action, run.truth);
  }

  function taskCode(task) {
    return LABELS.plan[task.id] || (task.task_id ? `${task.task_id}` : task.id);
  }

  function decisionName(decision) {
    return typeof decision === "string" ? "Không báo giá" : `Báo giá ${decision}`;
  }

  function actionName(action) {
    if (action.kind === "decide") return decisionName(action.decision);
    return LABELS.tasks[action.id];
  }

  function header() {
    const tabs = VIEWS.map(
      ([id, label]) =>
        `<button class="tab" data-msg="view:${id}" aria-current="${state.view === id ? "page" : "false"}">${label}</button>`,
    ).join("");
    return `<header class="top">
      <div class="brand"><h1>Koffer: nên thu thập thêm hay báo giá ngay?</h1>
      <p>Bộ khuyến nghị MDP cho báo giá bảo trì linh kiện máy bay, tái hiện Voorberg et al. (2021).</p></div>
      <nav class="tabs" aria-label="Màn hình">${tabs}</nav></header>`;
  }

  function toolbar() {
    const options = [
      `<option value="sample"${state.caseId === "sample" ? " selected" : ""}>Hồ sơ mẫu</option>`,
      ...data.table6.map(
        (row) =>
          `<option value="${row.instance}"${state.caseId === String(row.instance) ? " selected" : ""}>Trường hợp ${row.instance}, Bảng 6</option>`,
      ),
    ];
    if (state.caseId === "random") options.unshift('<option value="random" selected>Hồ sơ ngẫu nhiên</option>');
    const variants = Object.keys(data.koffer.variants)
      .map(
        (id) =>
          `<button class="seg" data-msg="variant:${id}" aria-pressed="${state.variant === id}">${VARIANT_LABELS[id]}</button>`,
      )
      .join("");
    return `<div class="toolbar">
      <div class="field"><label for="case-select">Hồ sơ</label>
        <div class="row"><select id="case-select" data-change="case">${options.join("")}</select>
        <button class="ghost" data-msg="random:">Bốc ngẫu nhiên</button></div></div>
      <div class="field"><span class="label" id="y-label">Hàm lợi nhuận Y</span>
        <div class="segments" role="group" aria-labelledby="y-label">${variants}</div></div>
    </div>`;
  }

  function caseFile() {
    const s = solver();
    const run = state.run;
    const finished = run.decision !== null;
    const tags = s.attributes
      .map((attr) => {
        const digit = s.digitOf(run.state, attr.id);
        const known = digit !== 0;
        const shown = known ? attr.values[digit - 1] : finished ? run.truth[attr.id] : "?";
        const note = known ? `đã biết` : finished ? "chưa từng mua, giá trị thật" : `mua với giá ${number(attr.cost, 0)}`;
        return `<li class="tag${known ? " known" : ""}${!known && finished ? " revealed" : ""}">
          <span class="code">${attr.id}</span>
          <span class="name">${LABELS.attributes[attr.id]}</span>
          <span class="val">${shown}</span>
          <span class="note">${note}</span></li>`;
      })
      .join("");
    const plan = s.plan
      .map((item) => {
        const done = s.isDone(run.state, item.id);
        return `<li class="${done ? "done" : ""}"><span class="tick" aria-hidden="true">${done ? "✓" : ""}</span>
          <span>${LABELS.tasks[item.id]}</span><span class="sr">${done ? "đã xong" : "chưa làm"}</span>
          <span class="num">${number(item.cost, 0)}</span></li>`;
      })
      .join("");
    return `<section class="panel" aria-labelledby="file-h"><h2 id="file-h">Thông tin hồ sơ</h2>
      <ul class="tags">${tags}</ul>
      <h3>Thủ tục và giai đoạn</h3><ul class="plan">${plan}</ul></section>`;
  }

  function actionRow(action, best, top) {
    const s = solver();
    const isBest = action.kind === best.kind && action.id === best.id && action.decision === best.decision;
    const gap = action.q - top;
    const message = action.kind === "do" ? `do:${action.id}` : `decide:${action.decision}`;
    const task = action.kind === "do" ? s.tasks.find((item) => item.id === action.id) : null;
    const code = task ? taskCode(task) : "";
    const detail = task ? `Chi phí ${number(task.cost, 0)}` : "Kết thúc hồ sơ";
    const gapText = Math.abs(gap) < 0.05 ? "ngang mức tốt nhất" : `kém ${number(-gap)}`;
    return `<li><button class="action${isBest ? " best" : ""}" data-msg="${escapeHtml(message)}">
      <span class="a-code">${code}</span>
      <span class="a-main"><span class="a-name">${actionName(action)}${isBest ? '<span class="pill">Khuyến nghị</span>' : ""}</span>
      <span class="a-detail">${detail}</span></span>
      <span class="a-value"><span class="a-q">${number(action.q)}</span><span class="a-gap">${gapText}</span></span>
      </button></li>`;
  }

  function actionsPanel() {
    const s = solver();
    const run = state.run;
    const actions = s.actionValues(run.state).sort((a, b) => b.q - a.q);
    const best = s.recommended(run.state);
    const top = Math.max(...actions.map((action) => action.q));
    const decisions = actions.filter((action) => action.kind === "decide");
    const gathering = actions.filter((action) => action.kind === "do");
    const missing = s.missingRequired(run.state).map((task) => LABELS.tasks[task.id]);
    const decideBlock = decisions.length
      ? `<ul class="actions">${decisions.map((action) => actionRow(action, best, top)).join("")}</ul>`
      : `<p class="locked">Chưa được báo giá. Còn thiếu: ${missing.join("; ")}.</p>`;
    return `<section class="panel" aria-labelledby="act-h"><h2 id="act-h">Bước tiếp theo</h2>
      <div class="stats">
        <div><span class="s-label">Đã chi</span><span class="s-value">${number(run.cost)}</span></div>
        <div><span class="s-label">Lợi nhuận kỳ vọng còn lại</span><span class="s-value">${number(s.value(run.state))}</span></div>
        <div><span class="s-label">Kỳ vọng cả hồ sơ</span><span class="s-value">${number(s.value(run.state) - run.cost)}</span></div>
      </div>
      <h3>Báo giá cuối cùng</h3>${decideBlock}
      ${gathering.length ? `<h3>Làm thêm</h3><ul class="actions">${gathering.map((action) => actionRow(action, best, top)).join("")}</ul>` : ""}
      <p class="hint">Số lớn ở mỗi dòng là lợi nhuận kỳ vọng nếu chọn hành động đó rồi đi tiếp tối ưu, chưa trừ phần đã chi. Bạn có thể chọn khác khuyến nghị; hệ thống vẫn tính tiếp từ trạng thái mới.</p>
      </section>`;
  }

  function resultPanel() {
    const s = solver();
    const run = state.run;
    const revenue = s.realisedY(run.truth, run.decision);
    const mdp = s.simulate((current) => s.recommended(current), run.truth);
    const tree = s.simulate(s.treePolicy(data.tree), run.truth);
    const rows = [
      ["Bạn", run.decision, run.cost, revenue],
      ["Theo đúng MDP", mdp.decision, mdp.cost, mdp.revenue],
      ["Cây quyết định (Fig. 8)", tree.decision, tree.cost, tree.revenue],
    ]
      .map(
        ([name, decision, cost, income]) => `<tr><th scope="row">${name}</th><td>${decisionName(decision)}</td>
          <td class="num">${number(cost)}</td><td class="num">${number(income)}</td><td class="num strong">${number(income - cost)}</td></tr>`,
      )
      .join("");
    return `<section class="panel" aria-labelledby="res-h"><h2 id="res-h">Kết quả trên cùng hồ sơ</h2>
      <div class="scroll"><table><thead><tr><th scope="col">Cách làm</th><th scope="col">Quyết định</th>
      <th scope="col" class="num">Chi phí</th><th scope="col" class="num">Doanh thu</th><th scope="col" class="num">Lợi nhuận</th></tr></thead>
      <tbody>${rows}</tbody></table></div>
      <p class="hint">Doanh thu là Y tại giá trị thật của hồ sơ, vẫn nhân với xác suất báo giá được chấp nhận vì giá thị trường là ngẫu nhiên. MDP tốt nhất về kỳ vọng trên mọi hồ sơ, nên vẫn có thể thua trên một hồ sơ riêng lẻ.</p>
      <button class="primary" data-msg="restart:">Làm lại hồ sơ này</button></section>`;
  }

  function logPanel() {
    const run = state.run;
    if (!run.log.length) return "";
    const items = run.log
      .map(
        (entry) => `<li><span>${entry.action}</span>
          ${entry.followed ? '<span class="followed">theo khuyến nghị</span>' : `<span class="deviated">khác khuyến nghị: ${entry.recommended}</span>`}</li>`,
      )
      .join("");
    return `<section class="panel log" aria-labelledby="log-h"><h2 id="log-h">Các bước đã làm</h2><ol>${items}</ol></section>`;
  }

  function kofferView() {
    const run = state.run;
    return `${toolbar()}<div class="grid">${caseFile()}<div class="stack">
      ${run.decision === null ? actionsPanel() : resultPanel()}${logPanel()}</div></div>`;
  }

  function toyView() {
    const spec = data.toy;
    const s = solverFor("toy", spec.default_variant);
    let current = s.rootState();
    const pickers = spec.attributes
      .map((attr) => {
        current = attr.id in state.toy ? s.observe(current, attr.id, state.toy[attr.id]) : current;
        const choices = [["", "Chưa biết"], ...attr.values.map((value) => [String(value), String(value)])]
          .map(([value, label]) => {
            const pressed = value === "" ? !(attr.id in state.toy) : state.toy[attr.id] === Number(value);
            return `<button class="seg" data-msg="toy:${attr.id}=${value}" aria-pressed="${pressed}">${label}</button>`;
          })
          .join("");
        return `<div class="field"><span class="label">${attr.id === "X1" ? "X₁" : "X₂"} (mỗi giá trị xác suất 0,5)</span><div class="segments">${choices}</div></div>`;
      })
      .join("");
    const best = s.recommended(current);
    const rows = s
      .actionValues(current)
      .map((action) => {
        const isBest = action.kind === best.kind && action.id === best.id && action.decision === best.decision;
        const name =
          action.kind === "decide"
            ? action.decision === 1 ? "Nhận (f = 1)" : "Từ chối (f = 0)"
            : `Mua thông tin ${action.id === "X1" ? "X₁" : "X₂"}, giá 0,5`;
        return `<tr class="${isBest ? "best-row" : ""}"><th scope="row">${name}${isBest ? '<span class="pill">Khuyến nghị</span>' : ""}</th><td class="num strong">${number(action.q, 2)}</td></tr>`;
      })
      .join("");
    return `<section class="panel narrow"><h2>Khi nào thông tin đáng mua?</h2>
      <p>Lợi nhuận Y = (X₂ − X₁)·f, với X₁ ∈ {0, 3} và X₂ ∈ {1, 4}. Chọn những gì đã biết để xem hành động nào tốt nhất.</p>
      <div class="toolbar plain">${pickers}</div>
      <p class="big"><span class="s-label">Lợi nhuận kỳ vọng tốt nhất</span><span class="s-value">${number(s.value(current), 2)}</span></p>
      <div class="scroll"><table><thead><tr><th scope="col">Hành động</th><th scope="col" class="num">Lợi nhuận kỳ vọng</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="note-box">Bài báo (mục 5.3) ghi lợi nhuận khi chưa có thông tin là ${number(data.paper_toy.value_no_info)} và kết luận nên mua X₂. Tính lại, E[X₂ − X₁] = 1,0 còn mua X₂ chỉ cho 0,75, nên quyết định ngay mới là tối ưu.</p></section>`;
  }

  function aboutView() {
    const rows = data.table5
      .map(
        (row) => `<tr><th scope="row">${row.label}</th><td class="num">${row.paper}</td><td class="num">${row.margin_all}</td><td class="num">${row.margin_repair}</td></tr>`,
      )
      .join("");
    return `<section class="panel narrow"><h2>Mô hình này tính gì</h2>
      <p>Mỗi hồ sơ có 9 thuộc tính chưa biết và 14 mục kế hoạch có chi phí. Quy nạp ngược tính lợi nhuận kỳ vọng tối ưu cho mọi trạng thái, nên tại mỗi bước có thể so sánh việc mua thêm thông tin với việc báo giá ngay. Trang này tự giải mô hình ngay trên trình duyệt của bạn, không gửi dữ liệu đi đâu.</p>
      <p class="formula">Y = E · B · H · P(D ≥ f) · [f − A(1 − 0,2G) − F − I]</p>
      <p>Đây là công thức in ở trang 10 của bài. Bản đối chứng tính F và I một lần cho mỗi hợp đồng: Y = E · B · H · P(D ≥ f) · [f − A(1 − 0,2G)] − F − I.</p>
      <h3>So với Bảng 5 của bài báo</h3>
      <div class="scroll"><table><thead><tr><th scope="col">Chỉ số</th><th scope="col" class="num">Bài báo</th><th scope="col" class="num">Công thức in</th><th scope="col" class="num">Đối chứng</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p>Cây quyết định khớp chính xác phần không phụ thuộc Y (chi phí, số trạng thái kết thúc). Lợi nhuận thì không khớp với công thức nào đã thử, nên đây là tái hiện về phương pháp và xu hướng, chưa phải về con số.</p>
      <p class="hint">Voorberg, Eshuis, van Jaarsveld, van Houtum (2021), Decision Support Systems 151, 113632. Đồ án CS2208, UIT.</p></section>`;
  }

  function html() {
    const body = state.view === "koffer" ? kofferView() : state.view === "toy" ? toyView() : aboutView();
    return `${header()}<main>${body}</main>`;
  }

  return { dispatch, html, state, solver };
}

if (typeof module !== "undefined") module.exports = { createApp, seededRandom, drawCase, number };
