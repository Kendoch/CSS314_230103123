"""Experiment B: frequent writes to one shared counter under a lock."""
import argparse
import time
from multiprocessing import Process, Value, Lock
from statistics import median
from common import CORES, save_results


def contended_worker(shared_counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            shared_counter.value += 1


def run_contended(p, total_increments=2_000_000):
    # Divide remainder too, so all inputs produce exactly total_increments.
    allocations = [total_increments // p + (i < total_increments % p) for i in range(p)]
    counter = Value('i', 0, lock=False)
    lock = Lock()
    procs = [Process(target=contended_worker, args=(counter, lock, n)) for n in allocations]
    start = time.perf_counter()
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()
    elapsed = time.perf_counter() - start
    if any(proc.exitcode != 0 for proc in procs):
        raise RuntimeError('At least one worker process failed')
    assert counter.value == total_increments, (counter.value, total_increments)
    return elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--increments', type=int, default=2_000_000)
    parser.add_argument('--repeats', type=int, default=1)
    args = parser.parse_args()
    if min(args.increments, args.repeats) < 1:
        parser.error('All numeric arguments must be positive')
    times = {}
    for p in CORES:
        attempts = [run_contended(p, args.increments) for _ in range(args.repeats)]
        times[p] = median(attempts)
        print(f'Experiment B: P={p}, measured time={times[p]:.4f}s')
    save_results('experiment_b.csv', times)


if __name__ == '__main__':
    main()
