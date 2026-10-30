"""Experiment A: parallel compute with fixed 0.40-second serial delay."""
import argparse
import math
import time
from multiprocessing import Pool
from statistics import median
from common import CORES, save_results


def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))


def run_experiment(workers, total_chunks=16, chunk_size=2_000_000):
    start = time.perf_counter()
    time.sleep(0.40)
    with Pool(processes=workers) as pool:
        results = pool.map(heavy_math, [chunk_size] * total_chunks)
    assert len(results) == total_chunks and all(math.isfinite(v) for v in results)
    return time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chunks', type=int, default=16)
    parser.add_argument('--chunk-size', type=int, default=2_000_000)
    parser.add_argument('--repeats', type=int, default=1)
    args = parser.parse_args()
    if min(args.chunks, args.chunk_size, args.repeats) < 1:
        parser.error('All numeric arguments must be positive')
    times = {}
    for p in CORES:
        attempts = [run_experiment(p, args.chunks, args.chunk_size) for _ in range(args.repeats)]
        times[p] = median(attempts)
        print(f'Experiment A: P={p}, measured time={times[p]:.4f}s')
    save_results('experiment_a.csv', times)


if __name__ == '__main__':
    main()
