import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Clover'))
from utils import run_dafny, is_dafny_verified


def extract_spec(dfy_path):
    with open(dfy_path) as f:
        lines = f.readlines()

    signature = None
    returns_clause = None
    requires = []
    ensures = []

    for line in lines:
        s = line.strip()
        if s.startswith('method ') or s.startswith('function method '):
            signature = s
        elif s.startswith('returns '):
            returns_clause = s[len('returns '):]
        elif s.startswith('requires '):
            requires.append(s[len('requires '):].rstrip())
        elif s.startswith('ensures '):
            ensures.append(s[len('ensures '):].rstrip())
        elif s == '{':
            break

    return {
        'signature': signature,
        'returns': returns_clause,
        'requires': requires,
        'ensures': ensures,
    }


def parse_method_params(signature):
    m = re.match(r'(?:function\s+)?method\s+\w+\s*\((.*?)\)\s*(?:returns\s*\((.*?)\))?', signature)
    if not m:
        return '', ''
    return (m.group(1) or '').strip(), (m.group(2) or '').strip()


def strip_old(clause):
    return re.sub(r'\bold\(([^)]+)\)', r'\1', clause)


def build_entailment_lemma(spec, assumed_ensures, prove_ensures):
    sig = spec['signature']
    if sig is None:
        return None

    in_params, out_params = parse_method_params(sig)
    all_params_parts = [p for p in [in_params, out_params] if p]
    all_params = ', '.join(all_params_parts)

    has_array = 'array' in sig

    lines = [f'lemma EntailCheck({all_params})']
    if has_array:
        lines.append('  reads *')
    for req in spec['requires']:
        lines.append(f'  requires {strip_old(req)}')
    for clause in assumed_ensures:
        lines.append(f'  requires {strip_old(clause)}')
    for clause in prove_ensures:
        lines.append(f'  ensures {strip_old(clause)}')
    lines.append('{}')

    return '\n'.join(lines)


def check_implication(spec, from_ensures, to_ensures, dafny_path):
    lemma = build_entailment_lemma(spec, from_ensures, to_ensures)
    if lemma is None:
        return None
    out, _ = run_dafny(lemma, dafny_path)
    return is_dafny_verified(out)


def classify(orig_spec, mut_spec, dafny_path):
    orig_ens = orig_spec['ensures']
    mut_ens = mut_spec['ensures']

    if orig_ens == mut_ens:
        return 'equivalent'

    fwd = check_implication(orig_spec, orig_ens, mut_ens, dafny_path)
    if fwd is None:
        return 'error'
    bwd = check_implication(orig_spec, mut_ens, orig_ens, dafny_path)
    if bwd is None:
        return 'error'

    if fwd and not bwd:
        return 'strictly_weaker'
    elif fwd and bwd:
        return 'equivalent'
    else:
        return 'incomparable'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dafny-path', required=True)
    parser.add_argument('--generated-dir', default='datasets/generated_c6')
    parser.add_argument('--original-dir', default='Clover/dataset/CloverBench/textbook_algo')
    parser.add_argument('--clover-log', default='Clover/exp_results_k_1.log')
    args = parser.parse_args()

    with open(args.clover_log) as f:
        clover_results = json.load(f)['gt']

    results = []

    for name in sorted(os.listdir(args.generated_dir)):
        mut_path = os.path.join(args.generated_dir, name, f'{name}.dfy')
        orig_path = os.path.join(args.original_dir, name, f'{name}_strong.dfy')

        if not os.path.exists(mut_path) or not os.path.exists(orig_path):
            continue
        if name not in clover_results:
            continue

        orig_spec = extract_spec(orig_path)
        mut_spec = extract_spec(mut_path)

        if not orig_spec['ensures'] and not mut_spec['ensures']:
            label = 'no_ensures'
        else:
            label = classify(orig_spec, mut_spec, args.dafny_path)

        clover_passed = clover_results[name][0]
        results.append({'name': name, 'weakening': label, 'clover_passed': clover_passed})
        print(f'{name:30} weakening={label:20} clover_passed={clover_passed}')

    # 2x2 table: strictly_weaker vs other × clover missed vs caught
    A = sum(1 for r in results if r['weakening'] == 'strictly_weaker' and r['clover_passed'])
    B = sum(1 for r in results if r['weakening'] == 'strictly_weaker' and not r['clover_passed'])
    C = sum(1 for r in results if r['weakening'] != 'strictly_weaker' and r['clover_passed'])
    D = sum(1 for r in results if r['weakening'] != 'strictly_weaker' and not r['clover_passed'])

    print('\n' + '=' * 60)
    print('WEAKENING LABEL COUNTS')
    for label in ['strictly_weaker', 'equivalent', 'incomparable', 'error', 'no_ensures']:
        count = sum(1 for r in results if r['weakening'] == label)
        if count:
            print(f'  {label}: {count}')

    print('\n2x2 CROSS-TABULATION')
    print(f'{"":26} {"Clover MISSED":>14} {"Clover CAUGHT":>14}')
    print(f'{"Strictly weaker spec":26} {A:>14} {B:>14}')
    print(f'{"Equivalent / other":26} {C:>14} {D:>14}')

    total = A + B + C + D
    print(f'\nSTATS (n={total})')
    if A + B > 0:
        print(f'  Weakening rate:                  {A+B}/{total} = {(A+B)/total:.1%}')
        print(f'  Weakened → Clover missed:        {A}/{A+B} = {A/(A+B):.1%}')
    if A + B > 0:
        print(f'  Precision (weaker predicts miss): {A}/{A+B} = {A/(A+B):.1%}')
    if A + C > 0:
        print(f'  Recall (misses explained by weak): {A}/{A+C} = {A/(A+C):.1%}')


if __name__ == '__main__':
    main()
