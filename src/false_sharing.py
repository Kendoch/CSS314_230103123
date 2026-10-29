"""False-sharing benchmark using true shared 64-bit counters and Python increments.
On macOS spawn launches separate child processes.
"""
import csv
import ctypes
import json
import multiprocessing as mp
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
K = 5_000_000

def increment(buf, idx, iterations):
    # Each Python iteration performs a real shared-memory load and store.
    for _ in range(iterations):
        buf[idx] += 1


def local_increment(iterations):
    value = 0
    for _ in range(iterations):
        value += 1
    return value


def worker(shared, idx, iterations, mode):
    data = np.frombuffer(shared, dtype=np.int64)
    if mode == 'privatized':
        data[idx] = local_increment(iterations)
    else:
        increment(data, idx, iterations)


def run(mode,p):
    arr=mp.RawArray(ctypes.c_int64, max(8, p*8))
    children=[]
    start=time.perf_counter()
    for i in range(p):
        idx=i*8 if mode == 'padded' else i
        child=mp.Process(target=worker, args=(arr,idx,K,mode))
        child.start(); children.append(child)
    for child in children:
        child.join()
        if child.exitcode != 0: raise RuntimeError(f'worker exited with {child.exitcode}')
    duration=time.perf_counter()-start
    vals=np.frombuffer(arr,dtype=np.int64)
    counts=int(sum(int(vals[i*8 if mode=='padded' else i]) for i in range(p)))
    if counts != p*K: raise AssertionError((mode,p,counts,p*K))
    return duration,counts


def main():
    mp.set_start_method('spawn', force=True)
    # Child processes read/write the shared RawArray, no per-counter lock.
    rows=[]
    for mode in ['unpadded','padded','privatized']:
        base=None
        for p in [1,2,4,8]:
            runtime,counts=run(mode,p)
            if p==1: base=runtime
            speedup=base/runtime
            e=((1/speedup)-(1/p))/(1-(1/p)) if p>1 else None
            rows.append([mode,p,K,runtime,speedup,e,counts])
            print(f'{mode:11} P={p} time={runtime:.3f}s S={speedup:.3f} e={e}')
    with (ROOT/'results/false_sharing_karp_flatt.tsv').open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t');w.writerow(['mode','processes','iterations_per_process','seconds','speedup','karp_flatt','total_count']);w.writerows(rows)
    print('NOTE: Runtime includes process spawn, Python interpreter overhead, and OS scheduling; collapse is not guaranteed on every Apple Silicon model.')

if __name__=='__main__': main()
