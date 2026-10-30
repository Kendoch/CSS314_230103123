# CS482 Practice Lab — Karp–Flatt Scalability Diagnostics

## Machine / environment

- Machine: Apple M1
- Operating system: macOS-15.4.1-arm64-arm-64bit
- Python: 3.12.7
- Logical execution cores: 8
- Physical cores (macOS sysctl): 8
- Runtime measurements: recorded locally on this machine, not theoretical examples.

## Empirical results

| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Architectural diagnosis |
|---|---:|---:|---:|---:|---:|---|
| A: Serial Tail | 4.1163 | 2.3355 | 1.5162 | 0.1347 | 0.1578 | Fixed 0.40-second sequential delay; inspect whether e(2) and e(4) are similar. |
| B: Lock Contention | 2.3159 | 6.2599 | 7.7006 | 4.4060 | 4.1002 | Per-increment shared locking; inspect negative speedup and increasing e. |
| C: Privatized State | 0.6131 | 0.3835 | 0.3608 | 0.2512 | 0.4513 | Private accumulation and one final reduction; inspect recovered speedup. |

## Instructor rubric checks

- **A:** e(4)/e(2) = 1.171; rubric target [0.80, 1.25].
- **B:** T4 > T1: True; e(4) > e(2): False.
- **C:** T4 < T1: True; E4 = 42.48% (rubric target >70%).

## Interpretation

Experiment A introduces an intentional fixed serial pause. A roughly stable Karp–Flatt metric is compatible with a fixed serial component. Experiment B forces repeated synchronization on one shared counter, creating lock contention. Experiment C removes the per-increment lock with local accumulation, then reduces the partial totals. Measured performance depends on scheduling, startup overhead, core architecture, and system load; target signatures are not guaranteed.

## Reproduction

```bash
python3 exp_a_serial.py
python3 exp_b_contention.py
python3 exp_c_fixed.py
python3 make_results.py
```
