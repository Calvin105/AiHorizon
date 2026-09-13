"""Oracle test: each sample encodes a known defect, so the measurements must recover it."""
import sys, pathlib
sys.path.insert(0, "/home/calvinkhoo/Documents/GitHub/AiHorizon/vision")
from main import measure_image

base = pathlib.Path("/home/calvinkhoo/Documents/GitHub/AiHorizon/vision/samples")
rows = {}
for kind in ("good", "inconsistent", "missing", "spreading", "undersized", "misaligned"):
    r = measure_image((base / f"{kind}.png").read_bytes())
    s = {x["key"]: x["value"] for x in r["signals"]}
    rows[kind] = s
    print(f"{kind:14} n={s['blob_count']:2} cv={s['size_cv']:.3f} circ={s['mean_circularity']:.3f} "
          f"pos={s['position_deviation_px']:.1f} spread={s['spread_index']:.2f} miss={s['missing_count']} "
          f"over={s['oversized_count']} under={s['undersized_count']} irreg={s['irregular_count']}")

print("\n--- oracle assertions ---")
checks = [
    ("good is repeatable",        rows["good"]["size_cv"] < 0.10),
    ("good flags nothing",        rows["good"]["oversized_count"] + rows["good"]["undersized_count"] + rows["good"]["irregular_count"] == 0),
    ("inconsistent is dispersed", rows["inconsistent"]["size_cv"] > 0.25),
    ("missing finds all 3",       rows["missing"]["missing_count"] == 3),
    ("missing stays repeatable",  rows["missing"]["size_cv"] < 0.10),
    ("spreading flags shape",     rows["spreading"]["irregular_count"] >= 5),
    ("spreading raises index",    rows["spreading"]["spread_index"] > 1.2),
    ("misaligned detects offset", rows["misaligned"]["position_deviation_px"] > 2.0),
    ("aligned reads near zero",   rows["good"]["position_deviation_px"] < 1.0),
]
for name, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
print(f"\n{sum(1 for _, ok in checks if ok)}/{len(checks)} passed")
