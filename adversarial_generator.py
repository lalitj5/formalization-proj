import os
import json
import argparse
import tempfile
import subprocess
from datetime import datetime

from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import TextBlock

from extractor import build_data

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

MAX_ATTEMPTS = 5
DAFNY_TIMEOUT = 30


# ── LLM ──────────────────────────────────────────────────────────────────────

def query(prompt: str, temperature: float = 0.7) -> str:
    result = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(b.text for b in result.content if isinstance(b, TextBlock))
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text.strip()


# ── Dafny ─────────────────────────────────────────────────────────────────────

def dafny_verify(dfy_content: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(suffix=".dfy", mode="w", delete=False) as f:
        f.write(dfy_content)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["dafny", "verify", tmp_path],
            capture_output=True, text=True, timeout=DAFNY_TIMEOUT,
        )
        output = result.stdout + result.stderr
        verified = result.returncode == 0 and "0 errors" in output
        return verified, ("" if verified else output.strip())
    except subprocess.TimeoutExpired:
        return False, "Dafny verification timed out"
    finally:
        os.unlink(tmp_path)


# ── Prompts ───────────────────────────────────────────────────────────────────

def prompt_c1(spec: str, strong_dfy: str) -> str:
    return f"""
<role_assignment>
Trickster
</role_assignment>

<task>
Subtly mutate the natural language docstring so it no longer accurately describes
the code. The change must be plausible — a reviewer should not immediately notice
the divergence. You may strengthen, weaken, or shift the described behavior.
Do NOT touch the Dafny code or annotations at all.
</task>

<original_docstring>
{spec}
</original_docstring>

<dafny_program>
{strong_dfy}
</dafny_program>

<return_instructions>
Return ONLY the mutated docstring — one or two sentences, no markdown, no commentary.
</return_instructions>
"""


def prompt_c2(spec: str, strong_dfy: str, error_feedback: str = "") -> str:
    feedback_block = f"""
<previous_attempt_failed>
Your last attempt did not pass Dafny verification. The error was:
{error_feedback}
Adjust the annotations so Dafny accepts the unchanged code.
</previous_attempt_failed>
""" if error_feedback else ""

    return f"""
<role_assignment>
Trickster
</role_assignment>

<task>
Weaken the formal annotations (requires/ensures/invariants) of the Dafny program
so they no longer fully capture the original spec. The implementation body must
remain completely unchanged. The weakened annotations must still pass Dafny
verification. The change should be subtle enough to fool a reviewer.
</task>

<original_spec>
{spec}
</original_spec>

<dafny_program>
{strong_dfy}
</dafny_program>
{feedback_block}
<return_instructions>
Return ONLY the complete modified Dafny method with weakened annotations and the
original unchanged body — no explanation, no markdown fences, no commentary.
</return_instructions>
"""


def prompt_c3_dfy(spec: str, strong_dfy: str, error_feedback: str = "") -> str:
    feedback_block = f"""
<previous_attempt_failed>
Your last attempt did not pass Dafny verification. The error was:
{error_feedback}
Adjust the annotations so Dafny accepts the unchanged code.
</previous_attempt_failed>
""" if error_feedback else ""

    return f"""
<role_assignment>
Trickster
</role_assignment>

<task>
Weaken the formal annotations (requires/ensures/invariants) of the Dafny program.
The implementation body must remain completely unchanged. The weakened annotations
must still pass Dafny verification. This is the first step of a two-step mutation —
focus only on the annotations for now.
</task>

<original_spec>
{spec}
</original_spec>

<dafny_program>
{strong_dfy}
</dafny_program>
{feedback_block}
<return_instructions>
Return ONLY the complete modified Dafny method with weakened annotations and the
original unchanged body — no explanation, no markdown fences, no commentary.
</return_instructions>
"""


def prompt_c3_doc(spec: str, weakened_dfy: str) -> str:
    return f"""
<role_assignment>
Trickster
</role_assignment>

<task>
A Dafny program has had its formal annotations weakened. Now rewrite the natural
language docstring so it is consistent with the weakened annotations rather than
the original spec. The new docstring should sound plausible and be consistent with
the weakened annotations, but no longer accurately describe the full original intent.
</task>

<original_docstring>
{spec}
</original_docstring>

<weakened_dafny_program>
{weakened_dfy}
</weakened_dafny_program>

<return_instructions>
Return ONLY the rewritten docstring — one or two sentences, no markdown, no commentary.
</return_instructions>
"""


# ── Per-class generators ──────────────────────────────────────────────────────

def generate_c1(item: dict, out_base: str) -> bool:
    name, spec, strong_dfy = item["name"], item["spec"], item["strong_dfy"]
    print(f"[{name}] C1 generating...", flush=True)

    mutated_doc = query(prompt_c1(spec, strong_dfy))
    save(out_base, name, strong_dfy=strong_dfy, mutated_doc=mutated_doc,
         corruption="C1", attempts=1)
    print(f"[{name}] C1 done")
    return True


def generate_c2(item: dict, out_base: str) -> bool:
    name, spec, strong_dfy = item["name"], item["spec"], item["strong_dfy"]
    print(f"[{name}] C2 generating...", flush=True)
    error_feedback = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        mutated_dfy = query(prompt_c2(spec, strong_dfy, error_feedback))
        verified, error_feedback = dafny_verify(mutated_dfy)
        if verified:
            save(out_base, name, strong_dfy=strong_dfy, mutated_dfy=mutated_dfy,
                 corruption="C2", attempts=attempt)
            print(f"[{name}] C2 verified on attempt {attempt}")
            return True
        print(f"[{name}] C2 attempt {attempt} failed verification")

    print(f"[{name}] C2 FAILED after {MAX_ATTEMPTS} attempts")
    return False


def generate_c3(item: dict, out_base: str) -> bool:
    name, spec, strong_dfy = item["name"], item["spec"], item["strong_dfy"]
    print(f"[{name}] C3 generating...", flush=True)
    error_feedback = ""
    weakened_dfy = None

    # Step 1: weaken annotation (same loop as C2)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        candidate = query(prompt_c3_dfy(spec, strong_dfy, error_feedback))
        verified, error_feedback = dafny_verify(candidate)
        if verified:
            weakened_dfy = candidate
            print(f"[{name}] C3 annotation verified on attempt {attempt}")
            break
        print(f"[{name}] C3 annotation attempt {attempt} failed verification")

    if weakened_dfy is None:
        print(f"[{name}] C3 FAILED — could not verify weakened annotation")
        return False

    # Step 2: rewrite docstring to match weakened annotation
    mutated_doc = query(prompt_c3_doc(spec, weakened_dfy))
    save(out_base, name, strong_dfy=strong_dfy, mutated_dfy=weakened_dfy,
         mutated_doc=mutated_doc, corruption="C3", attempts=1)
    print(f"[{name}] C3 done")
    return True


# ── Output ────────────────────────────────────────────────────────────────────

def save(
    out_base: str,
    name: str,
    strong_dfy: str,
    corruption: str,
    attempts: int,
    mutated_dfy: str = None,
    mutated_doc: str = None,
):
    out_dir = os.path.join(out_base, name)
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, f"{name}_strong.dfy"), "w") as f:
        f.write(strong_dfy)

    if mutated_dfy is not None:
        with open(os.path.join(out_dir, f"{name}.dfy"), "w") as f:
            f.write(mutated_dfy)

    if mutated_doc is not None:
        with open(os.path.join(out_dir, f"{name}_doc.txt"), "w") as f:
            f.write(mutated_doc)

    with open(os.path.join(out_dir, "category.txt"), "w") as f:
        f.write(f"generated_{corruption.lower()}")

    meta = {
        "name": name,
        "corruption": corruption,
        "model": MODEL,
        "attempts": attempts,
        "generated_at": datetime.utcnow().isoformat(),
    }
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--class", dest="corruption_class", required=True,
        choices=["C1", "C2", "C3"],
        help="Corruption class to generate"
    )
    args = parser.parse_args()

    out_base = os.path.join("datasets", f"generated_{args.corruption_class.lower()}")
    generators = {"C1": generate_c1, "C2": generate_c2, "C3": generate_c3}
    generate = generators[args.corruption_class]

    data = build_data()
    success, failed = [], []

    for key in sorted(data, key=int):
        item = data[key]
        ok = generate(item, out_base)
        (success if ok else failed).append(item["name"])

    print(f"\nDone. {len(success)} succeeded, {len(failed)} failed.")
    if failed:
        print("Failed:", failed)
