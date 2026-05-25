"""
Edit distance analysis comparing handwritten vs generated C6 mutations,
and correlating edit distance with Clover evasion rate.

Normalized edit distance = Levenshtein(original, mutated) / max(len(original), len(mutated))
Range: 0 (identical) to 1 (completely different). Lower = more subtle.
"""

import os
import json
import statistics


# ── Levenshtein distance ──────────────────────────────────────────────────────

def levenshtein(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if s1[i-1] == s2[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def normalized_edit_distance(s1: str, s2: str) -> float:
    return levenshtein(s1, s2) / max(len(s1), len(s2))


# ── Dafny splitting ───────────────────────────────────────────────────────────

def split_dafny(dfy: str) -> tuple[str, str]:
    """Split a single-method Dafny file into (annotations, body).

    Annotations = signature + requires/ensures/modifies (everything before the
    opening brace of the method body).
    Body = everything from the opening brace to the end.
    """
    idx = dfy.index("{")
    return dfy[:idx].strip(), dfy[idx:].strip()


# ── Data loading ──────────────────────────────────────────────────────────────

def load_pairs(generated_dir: str, original_dir: str, use_generated_original: bool = True):
    """
    Returns dict[name -> (total_ned, annotation_ned, body_ned)].

    generated_dir: folder containing mutated {name}/{name}.dfy files
    original_dir:  folder containing original {name}/{name}_strong.dfy
    use_generated_original: if True, original is {generated_dir}/{name}/{name}_strong.dfy
                            if False, original is {original_dir}/{name}/{name}_strong.dfy
    """
    results = {}
    for name in sorted(os.listdir(generated_dir)):
        item_dir = os.path.join(generated_dir, name)
        if not os.path.isdir(item_dir):
            continue

        mutated_path = os.path.join(item_dir, f"{name}.dfy")
        if use_generated_original:
            original_path = os.path.join(item_dir, f"{name}_strong.dfy")
        else:
            original_path = os.path.join(original_dir, name, f"{name}_strong.dfy")

        if not (os.path.exists(mutated_path) and os.path.exists(original_path)):
            continue

        original = open(original_path).read().strip()
        mutated = open(mutated_path).read().strip()

        try:
            orig_anno, orig_body = split_dafny(original)
            mut_anno, mut_body = split_dafny(mutated)
            anno_ned = normalized_edit_distance(orig_anno, mut_anno)
            body_ned = normalized_edit_distance(orig_body, mut_body)
        except ValueError:
            # Malformed file — skip per-section breakdown
            anno_ned = body_ned = None

        total_ned = normalized_edit_distance(original, mutated)
        results[name] = (total_ned, anno_ned, body_ned)

    return results


# ── Stats helpers ─────────────────────────────────────────────────────────────

def summary_vals(values: list[float], label: str):
    print(f"{label} (n={len(values)})")
    print(f"  mean   = {statistics.mean(values):.4f}")
    print(f"  median = {statistics.median(values):.4f}")
    print(f"  stdev  = {statistics.stdev(values):.4f}")
    print(f"  min    = {min(values):.4f}")
    print(f"  max    = {max(values):.4f}")


def summary(pairs: dict, label: str):
    total  = [v[0] for v in pairs.values()]
    annos  = [v[1] for v in pairs.values() if v[1] is not None]
    bodies = [v[2] for v in pairs.values() if v[2] is not None]
    print(f"{label} (n={len(total)})")
    print(f"  {'':20}  {'total':>8}  {'annotation':>10}  {'body':>8}")
    print(f"  {'mean':<20}  {statistics.mean(total):>8.4f}  {statistics.mean(annos):>10.4f}  {statistics.mean(bodies):>8.4f}")
    print(f"  {'median':<20}  {statistics.median(total):>8.4f}  {statistics.median(annos):>10.4f}  {statistics.median(bodies):>8.4f}")
    print(f"  {'stdev':<20}  {statistics.stdev(total):>8.4f}  {statistics.stdev(annos):>10.4f}  {statistics.stdev(bodies):>8.4f}")
    print(f"  {'min':<20}  {min(total):>8.4f}  {min(annos):>10.4f}  {min(bodies):>8.4f}")
    print(f"  {'max':<20}  {max(total):>8.4f}  {max(annos):>10.4f}  {max(bodies):>8.4f}")


def histogram(hw: dict, gen: dict, field: int = 0, field_label: str = "total"):
    buckets = [
        (0.00, 0.05, "0–5%  "),
        (0.05, 0.10, "5–10% "),
        (0.10, 0.20, "10–20%"),
        (0.20, 0.30, "20–30%"),
        (0.30, 0.50, "30–50%"),
        (0.50, 1.01, "50%+  "),
    ]
    hw_vals  = [v[field] for v in hw.values()  if v[field] is not None]
    gen_vals = [v[field] for v in gen.values() if v[field] is not None]

    print(f"\n[{field_label}]")
    print(f"{'Range':<10}  {'Handwritten':^26}  {'Generated':^26}")
    print("-" * 66)
    for lo, hi, label in buckets:
        hw_c  = sum(1 for v in hw_vals  if lo <= v < hi)
        gen_c = sum(1 for v in gen_vals if lo <= v < hi)
        print(f"{label}   {'█' * hw_c:<20} {hw_c:>3}    {'█' * gen_c:<20} {gen_c:>3}")


def evasion_by_bin(gen: dict, clover_results: dict):
    bins = [
        (0.00, 0.05, "0–5%  "),
        (0.05, 0.10, "5–10% "),
        (0.10, 0.20, "10–20%"),
        (0.20, 1.01, "20%+  "),
    ]

    for field, field_label in [(0, "total"), (1, "annotation"), (2, "body")]:
        rows = [
            (name, v[field], clover_results[name][0])
            for name, v in gen.items()
            if name in clover_results and v[field] is not None
        ]
        print(f"\n[{field_label}]")
        print(f"{'Range':<10}  {'Fooled':>8}  {'Caught':>8}  {'Evasion %':>10}")
        print("-" * 42)
        for lo, hi, label in bins:
            fooled = sum(1 for _, d, p in rows if lo <= d < hi and p)
            caught = sum(1 for _, d, p in rows if lo <= d < hi and not p)
            total  = fooled + caught
            pct    = f"{fooled / total * 100:.1f}%" if total else "—"
            print(f"{label}  {fooled:>8}  {caught:>8}  {pct:>10}")

        fooled_dists = [d for _, d, p in rows if p]
        caught_dists = [d for _, d, p in rows if not p]
        print(f"  mean   fooled={statistics.mean(fooled_dists):.4f}  caught={statistics.mean(caught_dists):.4f}")
        print(f"  median fooled={statistics.median(fooled_dists):.4f}  caught={statistics.median(caught_dists):.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    handwritten = load_pairs(
        generated_dir="datasets/adversarial_incorrect/C6",
        original_dir="datasets/textbook_algo",
        use_generated_original=False,
    )
    generated = load_pairs(
        generated_dir="datasets/generated_c6",
        original_dir=None,
        use_generated_original=True,
    )

    output_path = "edit_distance_results.txt"
    tee = open(output_path, "w")
    original_stdout = sys.stdout

    class Tee:
        def write(self, msg):
            original_stdout.write(msg)
            tee.write(msg)
        def flush(self):
            original_stdout.flush()
            tee.flush()

    sys.stdout = Tee()

    print("=" * 60)
    print("EDIT DISTANCE DISTRIBUTIONS")
    print("=" * 60)
    summary(handwritten, "Handwritten C6")
    print()
    summary(generated, "Generated C6")

    for field, label in [(0, "total"), (1, "annotation"), (2, "body")]:
        histogram(handwritten, generated, field=field, field_label=label)

    clover_log = "Clover/exp_results_k_1.log"
    if os.path.exists(clover_log):
        with open(clover_log) as f:
            clover_results = json.load(f)["gt"]
        print("\n" + "=" * 60)
        print("EDIT DISTANCE vs CLOVER EVASION (generated C6)")
        print("=" * 60)
        evasion_by_bin(generated, clover_results)
    else:
        print(f"\nNo Clover results found at {clover_log} — skipping evasion analysis.")

    sys.stdout = original_stdout
    tee.close()
    print(f"Results written to {output_path}")
