"""64-bit stride read latency in nanoseconds per touched element."""
import csv
import json
import time
from pathlib import Path
import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[1]

@njit(cache=True)
def sum_stride(data, stride):
    acc = 0.0
    for i in range(0, len(data), stride):
        acc += data[i]
    return acc


def main():
    params = json.loads((ROOT/'results/salted_params.json').read_text())
    data = np.ones(params['buffer_elements'], dtype=np.float64)
    sum_stride(data[:16], 1)  # JIT startup outside timing
    with (ROOT/'results/stride_results.tsv').open('w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['stride', 'elements_touched', 'median_ns', 'ns_per_element', 'checksum'])
        for stride in [1, 2, 4, 8, 16, 32, 64, 128]:
            for _ in range(5): sum_stride(data, stride)
            durations = []
            for _ in range(5):
                start = time.perf_counter_ns(); checksum = sum_stride(data, stride)
                durations.append(time.perf_counter_ns()-start)
            median = int(np.median(durations))
            touched = (len(data) + stride - 1)//stride
            writer.writerow([stride, touched, median, median/touched, checksum])
            print(f'stride={stride:3} ns/element={median/touched:.4f}')

if __name__ == '__main__': main()
