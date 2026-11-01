"""Phase 3: solve the full Koffer MDP with solve_array, save results/policy_koffer*.npz and results/runtime.json."""
from __future__ import annotations

import ctypes
import json
import os
import platform
import sys
import time
from ctypes import wintypes
from pathlib import Path

import numba
import numpy as np

from dipmdp.data import load_koffer, load_paper_results
from dipmdp.model import DIPModel
from dipmdp.solver import TIE_TOLERANCE, save_solution, solve_array

RESULTS = Path(__file__).resolve().parents[1] / "results"
# The chosen variant (assumption A3) comes first and owns the default file name.
Y_VARIANTS = {"margin_all": "policy_koffer.npz", "margin_repair": "policy_koffer_margin_repair.npz"}


def peak_memory_mb() -> float | None:
    """Peak working set of this process; None outside Windows, where this project runs."""
    if sys.platform != "win32":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    psapi = ctypes.WinDLL("psapi")
    kernel = ctypes.WinDLL("kernel32")
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    return round(counters.PeakWorkingSetSize / 2**20, 1)


def main() -> None:
    paper = load_paper_results()
    runs = {}
    for y_variant, file_name in Y_VARIANTS.items():
        model = DIPModel(load_koffer(), y_variant=y_variant, y_method="plugin")
        started = time.perf_counter()
        solution = solve_array(model)
        seconds = time.perf_counter() - started
        config = {
            "data": "data/koffer.yaml",
            "y_variant": y_variant,
            "y_expression": model.y_expression,
            "a1": "binomial",
            "a2": "p_on_second",
            "tie_break": "A9",
            "tie_tolerance": TIE_TOLERANCE,
            "solver": "solve_array",
            "random_seed": None,
        }
        save_solution(solution, RESULTS / file_name, config)
        runs[y_variant] = {
            "config": config,
            "policy_file": f"results/{file_name}",
            "n_states": model.state_space_size(),
            "n_reachable": solution.n_reachable,
            "solve_seconds": round(seconds, 3),
            "root_value": solution.root_value,
            "root_action": list(solution.root_action),
            "array_mb": round((solution.values.nbytes + solution.policy_codes.nbytes) / 2**20, 1),
        }
        print(y_variant, runs[y_variant]["root_value"], runs[y_variant]["root_action"], f"{seconds:.2f}s", flush=True)

    result = {
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "numba": numba.__version__,
        },
        "peak_process_memory_mb": peak_memory_mb(),
        "paper_runtime": paper["runtime"],
        "paper_state_space": paper["state_space"],
        "runs": runs,
    }
    (RESULTS / "runtime.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
