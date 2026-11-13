"""Check the deposited file inventory, questionnaire data and experimental inputs."""
import ast
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    allowed = set(manifest['files']) | {'manifest.json'}
    ignored = {'.git', '__pycache__', '.venv', 'generated', 'private_inputs'}
    present = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
               if p.is_file() and not set(p.relative_to(ROOT).parts) & ignored}
    assert present == allowed, ('Unexpected or missing files', sorted(present ^ allowed))
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
        assert Path(name).suffix.lower() not in {'.pdf', '.png', '.svg', '.pt', '.bin', '.zip', '.xlsx'}, name
        assert not name.startswith(('models/', 'results/replies/', 'results/reference/', 'figures/')), name
    items = rows(ROOT / 'metadata/survey_items.csv')
    expected = {'primary_student': 9566, 'middle_student': 3923, 'parent': 12266, 'teacher': 1546, 'principal': 95}
    assert len(items) == 43
    all_ids = set()
    for form, n in expected.items():
        selected = [r['variable'] for r in items if r['form'] == form]
        data = rows(ROOT / f'data/survey/raw/{form}.csv')
        assert len(data) == n
        assert list(data[0]) == ['record_id'] + selected
        assert len({r['record_id'] for r in data}) == n
        for record in data:
            assert record['record_id'] not in all_ids
            all_ids.add(record['record_id'])
            for name in selected:
                assert record[name] in {'', '1', '2', '3', '4', '5'}, (form, name)
    assert len(all_ids) == 27396
    pairs = rows(ROOT / 'metadata/survey_pairs.csv')
    assert len(pairs) == 7
    for pair in pairs:
        variables = {r['variable'] for r in items if r['form'] == pair['form']}
        assert {pair['x'], pair['y']} <= variables
    scenarios = rows(ROOT / 'prompts/scenarios.csv')
    assert len(scenarios) == len({r['id'] for r in scenarios}) == 60
    materialised = json.loads((ROOT / 'prompts/materialized_prompts.json').read_text(encoding='utf-8'))
    assert len(materialised) == 240
    assert len({(r['scenario_id'], r['condition']) for r in materialised}) == 240
    assert all(set(r) == {'scenario_id', 'condition', 'system', 'user'} for r in materialised)
    for script in (ROOT / 'scripts').glob('*.py'):
        ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
    print(f'Validated {len(allowed)} public files, 27,396 questionnaire records, 43 items and 240 input prompts.')
    print('The inventory contains survey observations/results and input/method materials only.')


if __name__ == '__main__':
    main()
