"""Policies to compare. (Phase 4)

Common interface: policy.act(state) -> action, given the current state only.

TODO(Phase 4):
- MDPPolicy(solution)
- DecisionTreePolicy(tree, model)       # Fig. 8; needs current state to know observed values
- RequiredOnlyPolicy(model)             # do required items only, then best decision on E[Y]
- CollectAllPolicy(model)               # acquire every attribute (respecting precedence), then decide
- MyopicVoIPolicy(model)                # one-step lookahead: acquire the attribute with the highest
                                        # (E[max_f E[Y]] after observing) - cost, if > 0; else decide
"""
