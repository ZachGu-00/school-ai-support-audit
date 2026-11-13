"""Reproduce this article's survey statistics from anonymised raw item responses."""
import argparse
import csv
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def save(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def value(text):
    return int(text) if text != '' else None


def wilson(k, n):
    if not n:
        return None, None
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0., centre - half), min(1., centre + half)


def compute():
    items = read(ROOT / 'metadata/survey_items.csv')
    pairs = read(ROOT / 'metadata/survey_pairs.csv')
    forms = list(dict.fromkeys(row['form'] for row in items))
    raw = {form: read(ROOT / f'data/survey/raw/{form}.csv') for form in forms}
    frequencies, marginals, samples = [], [], []
    for form in forms:
        selected = [row for row in items if row['form'] == form]
        samples.append({'form': form, 'role': selected[0]['role'], 'n': len(raw[form]),
                        'released_items': len(selected)})
        for item in selected:
            values = [value(row[item['variable']]) for row in raw[form]]
            counts = Counter(values)
            n = len(values) - counts[None]
            freq = {**item, 'n_total': len(values), 'n_missing': counts[None],
                    **{f'n_{i}': counts[i] for i in range(1, 6)}}
            frequencies.append(freq)
            marginals.append({'form': form, 'variable': item['variable'], 'n': n,
                'agree_pct': 100 * (counts[4] + counts[5]) / n if n else None,
                'undecided_pct': 100 * counts[3] / n if n else None,
                'disagree_pct': 100 * (counts[1] + counts[2]) / n if n else None})
    joint_counts, summary, plot, figure5, appendix = [], [], [], [], []
    for pair in pairs:
        observations = [(value(row[pair['x']]), value(row[pair['y']])) for row in raw[pair['form']]]
        complete = [(x, y) for x, y in observations if x is not None and y is not None]
        n = len(complete)
        counts = Counter(complete)
        for x in range(1, 6):
            for y in range(1, 6):
                joint_counts.append({'pair_id': pair['id'], 'form': pair['form'],
                                     'x_value': x, 'y_value': y, 'n': counts[x, y]})
        paired_rows = []
        for threshold, agree in [('primary', {4, 5}), ('strict', {5})]:
            nx = sum(x in agree for x, y in complete)
            ny = sum(y in agree for x, y in complete)
            nb = sum(x in agree and y in agree for x, y in complete)
            row = {'pair_id': pair['id'], 'form': pair['form'], 'threshold': threshold,
                'agree_values': '|'.join(map(str, sorted(agree))),
                'n_total': len(observations), 'n_complete': n,
                'n_missing_either': len(observations) - n,
                'n_missing_x': sum(x is None for x, y in observations),
                'n_missing_y': sum(y is None for x, y in observations),
                'n_missing_both': sum(x is None and y is None for x, y in observations),
                'n_x_agree': nx, 'n_y_agree': ny, 'n_both_agree': nb,
                'n_x_only': nx - nb, 'n_y_only': ny - nb,
                'n_neither_agree': n - nx - ny + nb, 'n_not_x_agree': n - nx}
            for metric, k, den in [('p_both_among_complete', nb, n), ('p_x_agree_among_complete', nx, n),
                ('p_y_agree_among_complete', ny, n), ('p_y_among_x_agree', nb, nx),
                ('p_x_among_y_agree', nb, ny), ('p_y_among_not_x_agree', ny - nb, n - nx)]:
                row[metric] = k / den if den else None
                row[metric + '_wilson_low'], row[metric + '_wilson_high'] = wilson(k, den)
            summary.append(row)
            paired_rows.append(row)
            plot.append({'pair_id': pair['id'], 'form': pair['form'], 'threshold': threshold,
                'n_complete': n, 'n_benefit_agree': nx, 'n_concern_agree': ny, 'n_both': nb,
                'benefit_agree_pct': 100 * nx / n, 'concern_agree_pct': 100 * ny / n,
                'both_pct': 100 * nb / n, 'concern_among_benefit_pct': 100 * nb / nx if nx else None})
            if threshold == 'primary':
                for group, k, den in [('benefit_not_endorsed', ny - nb, n - nx), ('benefit_endorsed', nb, nx)]:
                    lo, hi = wilson(k, den)
                    figure5.append({'pair_id': pair['id'], 'form': pair['form'], 'group': group,
                        'n_concern_endorsed': k, 'n_group': den, 'concern_pct': 100 * k / den if den else None,
                        'wilson_low_pct': 100 * lo if lo is not None else None,
                        'wilson_high_pct': 100 * hi if hi is not None else None})
        primary, strict = paired_rows
        appendix.append({'pair_id': pair['id'], 'form': pair['form'], 'n': n,
            'both_agree_pct': 100 * primary['p_both_among_complete'],
            'concern_given_benefit_pct': 100 * primary['p_y_among_x_agree'],
            'both_strict_pct': 100 * strict['p_both_among_complete']})
    return {'sample_counts.csv': samples, 'item_frequencies.csv': frequencies,
        'item_marginals.csv': marginals, 'joint_counts.csv': joint_counts, 'joint_summary.csv': summary,
        'joint_plot_data.csv': plot, 'figure5_data.csv': figure5, 'appendix_A4.csv': appendix}


def verify(folder, tables):
    cells = 0
    for name, rows in tables.items():
        expected = read(folder / name)
        if len(expected) != len(rows):
            raise AssertionError((name, 'row count'))
        for actual, wanted in zip(rows, expected):
            if set(actual) != set(wanted):
                raise AssertionError((name, 'columns'))
            for key, val in actual.items():
                if isinstance(val, (int, float)):
                    if not math.isclose(float(wanted[key]), val, rel_tol=1e-12, abs_tol=1e-12):
                        raise AssertionError((name, key, wanted[key], val))
                    cells += 1
                elif ('' if val is None else str(val)) != wanted[key]:
                    raise AssertionError((name, key))
    print(f'Verified {len(tables)} survey tables and {cells} numeric cells.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir', type=Path, default=ROOT / 'generated/survey')
    parser.add_argument('--verify', action='store_true', help='Compare recomputed statistics to results/survey.')
    args = parser.parse_args()
    tables = compute()
    if args.verify:
        verify(ROOT / 'results/survey', tables)
    for name, rows in tables.items():
        save(args.outdir / name, rows)
    print(f'Wrote {len(tables)} survey tables to {args.outdir}.')


if __name__ == '__main__':
    main()
