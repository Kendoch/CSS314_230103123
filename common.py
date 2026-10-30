"""Shared output helpers for the CS482 Karp–Flatt practice lab."""
from pathlib import Path
import csv

RESULTS_DIR = Path(__file__).resolve().parent / 'results'
CORES = (1, 2, 4)


def diagnostic_rows(times):
    baseline = times[1]
    return [
        {
            'workers': p,
            'runtime_s': f'{times[p]:.6f}',
            'speedup': f'{baseline / times[p]:.6f}',
            'efficiency_pct': f'{100 * baseline / times[p] / p:.4f}',
            'karp_flatt_e': '' if p == 1 else f'{((p * times[p] / baseline) - 1) / (p - 1):.6f}'
        }
        for p in CORES
    ]


def save_results(filename, times):
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / filename
    rows = diagnostic_rows(times)
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f'\nSaved: {path}')
    print('  P   Runtime (s)   Speedup   Efficiency (%)   Karp–Flatt e')
    for row in rows:
        print(f"{int(row['workers']):>3}   {float(row['runtime_s']):>11.4f}   {float(row['speedup']):>7.3f}   {float(row['efficiency_pct']):>14.2f}   {row['karp_flatt_e']:>12}")
