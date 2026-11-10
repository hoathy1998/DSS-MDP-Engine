// Runs the web demo code in Node for tests/test_web_demo.py.
// Usage: node web_demo_check.js <web dir> <output dir>
// Writes every reachable Koffer state's value and recommended action per variant, plus scripted UI checks.
const fs = require("fs");
const path = require("path");

const [webDir, outDir] = process.argv.slice(2);
const { buildSolver } = require(path.join(webDir, "solver.js"));
const { createApp, seededRandom } = require(path.join(webDir, "app.js"));
const { data, functions } = JSON.parse(fs.readFileSync(path.join(webDir, "demo_data.json"), "utf-8"));

const Y_FUNCTIONS = {};
for (const [model, variants] of Object.entries(functions)) {
  Y_FUNCTIONS[model] = {};
  for (const [variant, code] of Object.entries(variants)) Y_FUNCTIONS[model][variant] = (0, eval)(code);
}

function exportVariant(variant) {
  const started = Date.now();
  const solver = buildSolver(data.koffer, variant, Y_FUNCTIONS.koffer[variant]);
  const solveMs = Date.now() - started;
  const { tasks } = solver;
  const codes = [];
  const values = [];
  const indices = [];
  const ids = tasks.map((task) => task.id);
  const strides = new Array(tasks.length).fill(1);
  for (let i = tasks.length - 2; i >= 0; i--) strides[i] = strides[i + 1] * tasks[i + 1].radix;

  const state = solver.rootState();
  function visit(position) {
    if (position === tasks.length) {
      const done = (id) => state[ids.indexOf(id)] !== 0;
      const reachable = tasks.every((task, i) => !state[i] || task.preceding.every(done));
      if (!reachable) return;
      const action = solver.recommended(state);
      indices.push(state.reduce((total, digit, i) => total + digit * strides[i], 0));
      values.push(solver.value(state));
      codes.push(
        action.kind === "do" ? ids.indexOf(action.id) : tasks.length + data.koffer.decisions.indexOf(action.decision),
      );
      return;
    }
    for (let digit = 0; digit < tasks[position].radix; digit++) {
      state[position] = digit;
      visit(position + 1);
    }
    state[position] = 0;
  }
  visit(0);
  fs.writeFileSync(path.join(outDir, `${variant}.json`), JSON.stringify({ indices, values, codes, solveMs }));

  const tree = solver.treePolicy(data.tree);
  return data.table6.map((row) => {
    const truth = Object.fromEntries(data.koffer.attributes.map((attr, i) => [attr.id, row.final_state[i]]));
    const mdp = solver.simulate((current) => solver.recommended(current), truth);
    const treeRun = solver.simulate(tree, truth);
    return { instance: row.instance, mdp_profit: mdp.profit, mdp_decision: mdp.decision, tree_profit: treeRun.profit, tree_decision: treeRun.decision };
  });
}

function scriptedUi() {
  const app = createApp(data, Y_FUNCTIONS, buildSolver, seededRandom(7));
  const checks = {};
  checks.first_view_has_actions = app.html().includes("Bước tiếp theo") && app.html().includes("Khuyến nghị");
  checks.first_view_hides_truth = !/class="tag known"/.test(app.html());
  checks.first_view_blocks_deciding = app.html().includes("Chưa được báo giá");

  // Deviate first, then follow every recommendation to the end.
  app.dispatch(["do", "alpha"]);
  checks.cost_after_alpha = app.state.run.cost;
  checks.deviation_logged = app.html().includes("khác khuyến nghị");
  let steps = 0;
  while (app.state.run.decision === null && steps++ < 30) {
    const best = app.solver().recommended(app.state.run.state);
    app.dispatch(best.kind === "do" ? ["do", best.id] : ["decide", String(best.decision)]);
    app.html();
  }
  const end = app.html();
  checks.reached_decision = app.state.run.decision !== null;
  checks.result_compares_three = ["Bạn", "Theo đúng MDP", "Cây quyết định (Fig. 8)"].every((name) => end.includes(name));
  checks.nothing_undefined = !/undefined|NaN/.test(end);

  app.dispatch(["restart", ""]);
  checks.restart_clears = app.state.run.cost === 0 && app.state.run.log.length === 0;
  app.dispatch(["variant", "margin_repair"]);
  checks.variant_switched = app.state.variant === "margin_repair" && app.html().includes("Bước tiếp theo");
  app.dispatch(["case", "8"]);
  checks.table6_case_loaded = app.state.run.truth.A === 1700 && app.state.run.truth.I === 200;
  app.dispatch(["random", ""]);
  checks.random_case = app.state.caseId === "random" && !/undefined|NaN/.test(app.html());

  app.dispatch(["view", "toy"]);
  checks.toy_root_value = app.html().includes(">1,00<");
  app.dispatch(["toy", "X2=4"]);
  checks.toy_after_x2 = app.html().includes(">2,50<");
  app.dispatch(["toy", "X2="]);
  checks.toy_cleared = app.html().includes(">1,00<");
  app.dispatch(["view", "about"]);
  checks.about_has_table5 = app.html().includes("8.762,62") && app.html().includes("15.867,60");
  return checks;
}

const toy = buildSolver(data.toy, "toy", Y_FUNCTIONS.toy.toy);
const result = {
  table6: Object.fromEntries(Object.keys(functions.koffer).map((variant) => [variant, exportVariant(variant)])),
  toy_root_value: toy.value(toy.rootState()),
  toy_root_action: toy.recommended(toy.rootState()),
  ui: scriptedUi(),
};
fs.writeFileSync(path.join(outDir, "result.json"), JSON.stringify(result));
