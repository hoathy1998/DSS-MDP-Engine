// Backward induction for the web demo, a JavaScript port of dipmdp.solver and dipmdp.model.
// tests/test_web_demo.py compares it with the Python solver on every reachable Koffer state.
//
// A state is an array of digits, one per task in YAML order (plan items, then attributes):
// plan item 0/1, attribute 0 = unknown, k = k-th value. Tasks in `free` are required, nothing depends
// on them and Y ignores them, so the array solves without them and adds their cost back (as
// dipmdp.model.without_free_tasks does). That keeps Koffer at 1,350,000 cells instead of 8,100,000.

const TIE_TOLERANCE = 1e-9;

function buildSolver(spec, variant, yFunction) {
  const plan = spec.plan_items.map((item) => ({ ...item, isAttribute: false, radix: 2, probs: [1] }));
  const attributes = spec.attributes.map((attr) => ({ ...attr, isAttribute: true, radix: attr.values.length + 1 }));
  const tasks = [...plan, ...attributes];
  const position = new Map(tasks.map((task, i) => [task.id, i]));
  const free = new Set(spec.variants[variant].free);
  const accept = spec.accept;

  // Arrays over the tasks kept in the solved model.
  const kept = tasks.map((task, i) => i).filter((i) => !free.has(tasks[i].id));
  const keptBit = new Map(kept.map((taskIndex, bit) => [tasks[taskIndex].id, bit]));
  const strides = new Array(kept.length).fill(1);
  for (let i = kept.length - 2; i >= 0; i--) strides[i] = strides[i + 1] * tasks[kept[i + 1]].radix;
  const nStates = kept.length ? strides[0] * tasks[kept[0]].radix : 1;
  const keptAttributes = kept.filter((i) => tasks[i].isAttribute);
  const nInfo = keptAttributes.reduce((total, i) => total * tasks[i].radix, 1);

  const decisionTable = new Float64Array(nInfo * spec.decisions.length);
  for (let info = 0; info < nInfo; info++) {
    const digits = {};
    let remainder = info;
    for (let j = keptAttributes.length - 1; j >= 0; j--) {
      const task = tasks[keptAttributes[j]];
      digits[task.id] = remainder % task.radix;
      remainder = Math.floor(remainder / task.radix);
    }
    spec.decisions.forEach((decision, d) => {
      decisionTable[info * spec.decisions.length + d] = expectedY(digits, decision);
    });
  }

  function acceptProbability(decision, digit) {
    const row = accept[String(decision)];
    return digit ? row.by_value[digit - 1] : row.unknown;
  }

  function expectedY(digits, decision) {
    if (typeof decision === "string") return 0;
    const scope = { f: decision };
    for (const attr of attributes) {
      const digit = digits[attr.id] || 0;
      scope[attr.id] = digit ? attr.values[digit - 1] : attr.mean;
    }
    if (accept) scope.P = acceptProbability(decision, digits.D || 0);
    return yFunction(scope);
  }

  const preceding = kept.map((i) => tasks[i].preceding.reduce((mask, id) => mask | (1 << keptBit.get(id)), 0));
  const requiredMask = kept.reduce((mask, i, bit) => (tasks[i].required ? mask | (1 << bit) : mask), 0);
  const nDecisions = spec.decisions.length;
  const values = new Float64Array(nStates).fill(NaN);
  const digits = new Int32Array(kept.length);

  // A task's successors always have a larger index, so descending order sees them first.
  for (let index = nStates - 1; index >= 0; index--) {
    let remainder = index;
    let done = 0;
    for (let bit = 0; bit < kept.length; bit++) {
      const digit = Math.floor(remainder / strides[bit]);
      digits[bit] = digit;
      remainder -= digit * strides[bit];
      if (digit) done |= 1 << bit;
    }
    let reachable = true;
    for (let bit = 0; bit < kept.length; bit++) {
      if (digits[bit] && preceding[bit] & ~done) {
        reachable = false;
        break;
      }
    }
    if (!reachable) continue;

    let best = -Infinity;
    for (let bit = 0; bit < kept.length; bit++) {
      if (digits[bit] || preceding[bit] & ~done) continue;
      const task = tasks[kept[bit]];
      let q = -task.cost;
      for (let outcome = 0; outcome < task.probs.length; outcome++) {
        q += task.probs[outcome] * values[index + (outcome + 1) * strides[bit]];
      }
      if (q > best) best = q;
    }
    if (!(requiredMask & ~done)) {
      const info = index % nInfo;
      for (let d = 0; d < nDecisions; d++) {
        const q = decisionTable[info * nDecisions + d];
        if (q > best) best = q;
      }
    }
    values[index] = best;
  }

  function rootState() {
    return new Array(tasks.length).fill(0);
  }

  function isDone(state, id) {
    return state[position.get(id)] !== 0;
  }

  function keptIndex(state) {
    return kept.reduce((index, taskIndex, bit) => index + state[taskIndex] * strides[bit], 0);
  }

  function value(state) {
    let total = values[keptIndex(state)];
    for (const id of free) {
      if (!isDone(state, id)) total -= tasks[position.get(id)].cost;
    }
    return total;
  }

  function canDecide(state) {
    return tasks.every((task) => !task.required || isDone(state, task.id));
  }

  function missingRequired(state) {
    return tasks.filter((task) => task.required && !isDone(state, task.id));
  }

  function decisionValue(state, decision) {
    const info = keptAttributes.reduce((index, i) => index * tasks[i].radix + state[i], 0);
    return decisionTable[info * nDecisions + spec.decisions.indexOf(decision)];
  }

  function withDigit(state, id, digit) {
    const next = state.slice();
    next[position.get(id)] = digit;
    return next;
  }

  function actionValues(state) {
    const result = [];
    for (const task of tasks) {
      if (isDone(state, task.id) || !task.preceding.every((id) => isDone(state, id))) continue;
      let q = -task.cost;
      task.probs.forEach((p, outcome) => {
        q += p * value(withDigit(state, task.id, outcome + 1));
      });
      result.push({ kind: "do", id: task.id, q });
    }
    if (canDecide(state)) {
      for (const decision of spec.decisions) {
        result.push({ kind: "decide", decision, q: decisionValue(state, decision) });
      }
    }
    return result;
  }

  // Assumption A9: decisions first in YAML order, then lower cost, then YAML order.
  function tieRank(action) {
    if (action.kind === "decide") return [0, 0, spec.decisions.indexOf(action.decision)];
    return [1, tasks[position.get(action.id)].cost, position.get(action.id)];
  }

  function recommended(state) {
    const actions = actionValues(state);
    const best = Math.max(...actions.map((action) => action.q));
    const tied = actions.filter((action) => best - action.q <= TIE_TOLERANCE);
    tied.sort((a, b) => {
      const [ra, rb] = [tieRank(a), tieRank(b)];
      return ra[0] - rb[0] || ra[1] - rb[1] || ra[2] - rb[2];
    });
    return tied[0];
  }

  function perform(state, action, trueValues) {
    const task = tasks[position.get(action.id)];
    const digit = task.isAttribute ? task.values.indexOf(trueValues[task.id]) + 1 : 1;
    return withDigit(state, task.id, digit);
  }

  function realisedY(trueValues, decision) {
    if (typeof decision === "string") return 0;
    const scope = { ...trueValues, f: decision };
    if (accept) {
      const attr = attributes.find((a) => a.id === "D");
      scope.P = acceptProbability(decision, attr.values.indexOf(trueValues.D) + 1);
    }
    return yFunction(scope);
  }

  function simulate(act, trueValues) {
    let state = rootState();
    let cost = 0;
    const steps = [];
    for (;;) {
      const action = act(state);
      if (action.kind === "decide") {
        const revenue = realisedY(trueValues, action.decision);
        return { decision: action.decision, cost, revenue, profit: revenue - cost, state, steps };
      }
      cost += tasks[position.get(action.id)].cost;
      steps.push(action.id);
      state = perform(state, action, trueValues);
    }
  }

  function treePolicy(tree) {
    return (state) => {
      let node = tree.nodes[tree.root];
      for (;;) {
        if (node.type === "decide") return { kind: "decide", decision: node.decision };
        if (node.type === "check") {
          const digit = state[position.get(node.attribute)];
          if (!digit) return { kind: "do", id: node.attribute };
          const attr = tasks[position.get(node.attribute)];
          node = tree.nodes[node.branches[String(attr.values[digit - 1])]];
        } else {
          const pending = node.items.find((id) => !isDone(state, id));
          if (pending !== undefined) return { kind: "do", id: pending };
          node = tree.nodes[node.next];
        }
      }
    };
  }

  function observe(state, id, valueOfAttribute) {
    return withDigit(state, id, tasks[position.get(id)].values.indexOf(valueOfAttribute) + 1);
  }

  return {
    tasks, attributes, plan, rootState, isDone, value, canDecide, missingRequired, actionValues,
    recommended, perform, realisedY, simulate, treePolicy, observe,
    digitOf: (state, id) => state[position.get(id)],
  };
}

if (typeof module !== "undefined") module.exports = { buildSolver, TIE_TOLERANCE };
