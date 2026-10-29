"""Numba-compiled i-j-k vs i-k-j dense matrix multiply (M=N//2)."""
import json
import time
from pathlib import Path
import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[1]

@njit(cache=True)
def naive(a,b):
    n = a.shape[0]; c = np.zeros((n,n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            val = 0.0
            for k in range(n): val += a[i,k]*b[k,j]
            c[i,j] = val
    return c

@njit(cache=True)
def interchange(a,b):
    n = a.shape[0]; c = np.zeros((n,n), dtype=np.float64)
    for i in range(n):
        for k in range(n):
            v = a[i,k]
            for j in range(n): c[i,j] += v*b[k,j]
    return c


def bench(f,a,b):
    durations=[]; result=None
    for _ in range(3):
        t=time.perf_counter(); result=f(a,b)
        durations.append(time.perf_counter()-t)
    return float(np.median(durations)),result


def main():
    params=json.loads((ROOT/'results/salted_params.json').read_text())
    m=params['N']//2; rng=np.random.default_rng(params['seed'])
    a=rng.random((m,m)); b=rng.random((m,m))
    naive(a[:2,:2],b[:2,:2]); interchange(a[:2,:2],b[:2,:2])
    t1,c1=bench(naive,a,b); t2,c2=bench(interchange,a,b)
    diff=float(np.max(np.abs(c1-c2)))
    record={'student_id':params['student_id'], 'N':params['N'],'M':m,
        'naive_median_seconds':t1,'interchanged_median_seconds':t2,
        'speedup':t1/t2, 'max_absolute_error':diff,
        'allclose_atol_1e-12':bool(np.allclose(c1,c2,atol=1e-12,rtol=0)),
        'baseline_sha256_rounded_6':digest(c1), 'interchanged_sha256_rounded_6':digest(c2)}
    (ROOT/'results/loop_interchange.json').write_text(json.dumps(record,indent=2)+'\n')
    print(record)

def digest(matrix):
    import hashlib
    return hashlib.sha256(np.round(matrix,6).astype('<f8').tobytes()).hexdigest()

if __name__=='__main__': main()
