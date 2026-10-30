"""Experiment C: privatize counting and combine at the end."""
import argparse
import time
from multiprocessing import Pool
from statistics import median
from common import CORES, save_results


def private_worker(iterations):
    local_sum = 0
    for _ in range(iterations):
        local_sum += 1
    return local_sum


def run_privatized(p, total_increments=20_000_000):
    tasks = [total_increments // p + (i < total_increments % p) for i in range(p)]
    start = time.perf_counter()
    with Pool(processes=p) as pool:
        total = sum(pool.map(private_worker, tasks))
    elapsed = time.perf_counter() - start
    assert total == total_increments, (total, total_increments)
    return elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--increments', type=int, default=20_000_000)
    parser.add_argument('--repeats', type=int, default=1)
    args = parser.parse_args()
    if min(args.increments, args.repeats) < 1:
        parser.error('All numeric arguments must be positive')
    times = {}
    for p in CORES:
        attempts = [run_privatized(p, args.increments) for _ in range(args.repeats)]
        times[p] = median(attempts)
        print(f'Experiment C: P={p}, measured time={times[p]:.4f}s')
    save_results('experiment_c.csv', times)


if __name__ == '__main__':
    main()
