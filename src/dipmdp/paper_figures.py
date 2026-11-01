"""Bar heights read by eye from Fig. 7 (p. 12). Approximate; used only for comparison, never as input."""

FIG7_DECISIONS = {
    "mdp": {2200: 0.05, 2000: 0.22, 1800: 0.32, "No bid": 0.39},
    "tree": {2200: 0.065, 2000: 0.065, 1800: 0.13, "No bid": 0.73},
}
FIG7_TASKS = {
    "mdp": {"2": 0.59, "A": 0.60, "B": 0.0, "D": 0.59, "F": 0.09, "G": 0.41, "H": 0.0, "I": 0.18, "alpha": 0.60},
    "tree": {"2": 0.26, "A": 0.32, "B": 0.60, "D": 0.26, "F": 0.16, "G": 0.11, "H": 0.60, "I": 0.13, "alpha": 0.32},
}
