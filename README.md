# Formal Verification Adversarial Dataset

This project extends [Clover: Closed-Loop Verifiable Code Generation](https://arxiv.org/abs/2310.17807) by automating the generation of adversarial Dafny programs that diverge from their natural-language specifications while still passing Dafny's formal verifier.

## Background

Clover introduced CloverBench — a dataset of annotated Dafny programs paired with natural-language specs, along with handwritten adversarial variants organized by corruption class:

| Class | Code | Annotation | Docstring |
|-------|------|------------|-----------|
| C1 | — | — | mutated |
| C2 | — | weakened | — |
| C3 | — | weakened | mutated |
| C6 | mutated | weakened | — |

C6 is the hardest class: the code no longer satisfies the original spec, but a weakened annotation is crafted so Dafny still verifies it. The Clover paper handwrote these mutations. This project automates C6 generation using an LLM + Dafny verification loop.

## How It Works

`c6_generator.py` runs a generate-verify loop for each of the 62 problems in CloverBench:

1. Prompts Claude to subtly mutate the implementation and simultaneously weaken the annotations
2. Runs `dafny verify` on the output
3. If verification fails, feeds the error back to Claude and retries (up to 5 attempts)
4. Saves verified mutations to `datasets/generated_c6/`

**Results**: 60/62 problems successfully generated verified C6 mutations. `even_list` and `insert` failed — both have complex array invariants.

## Setup

```bash
pip install anthropic python-dotenv
# Create .env with: ANTHROPIC_API_KEY=sk-ant-...

python c6_generator.py   # generate verified C6 mutations
python tainter.py        # simpler mutation without verification loop
```

Requires [Dafny](https://github.com/dafny-lang/dafny) installed and on `PATH`.

## Dataset

```
datasets/
    textbook_algo/          # 62 ground-truth (spec, annotated Dafny) pairs
    textbook_algo_unit_tests/  # Dafny unit tests for ground truth
    adversarial_incorrect/  # handwritten adversarial variants (C1, C2, C3, C6)
    generated_c6/           # LLM-generated C6 mutations (this project)
```

## Findings

Generated mutations tend to be subtler than the handwritten ones. Examples:

- **`binary_search`**: handwritten replaced the algorithm with a broken linear scan; generated changed `< key` → `<= key` throughout, preserving the binary search structure
- **`avg`**: handwritten returned `a+b` outright; generated used `a/2 + b/2` with a disjunctive postcondition covering rounding cases
- **`abs`**: handwritten returned `0` for negatives; generated returned `1-x` with annotation weakened to `x+y>=0`
