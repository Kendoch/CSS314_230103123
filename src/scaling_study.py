"""Strong/weak scaling of a 5-point Jacobi stencil on Mac (spawn-safe)."""
import csv
import json
import math
import multiprocessing as mp
import time
from pathlib import Path
import numpy as np
import psutil
from numba import njit

ROOT=Path(__file__).resolve().parents[1]
REPEATS=15

@njit(cache=True)
def stencil_chunk(a, r0, r1):
    # Source has one extra halo row on every side.
    cols=a.shape[1];out=np.empty((r1-r0,cols-2),dtype=np.float64)
    for i in range(r0,r1):
        for j in range(1,cols-1):
            out[i-r0,j-1]=(a[i,j]*4.0+a[i-1,j]+a[i+1,j]+a[i,j-1]+a[i,j+1])/8.0
    return out


def work(arg):
    grid,start,stop=arg
    return start,stencil_chunk(grid,start,stop)


def matrix(n,seed):
    # Smooth deterministic matrix, exact same formula for all processor counts.
    i=np.arange(n+2,dtype=np.float64)[:,None]
    j=np.arange(n+2,dtype=np.float64)[None,:]
    return np.ascontiguousarray((i*0.1+j*0.01+seed*0.000001) % 17.0)


def split_rows(n,p):
    boundaries=np.linspace(1,n+1,p+1,dtype=int)
    return list(zip(boundaries[:-1], boundaries[1:]))


def run_case(n,p,seed,pool):
    grid=matrix(n,seed)
    tasks=[(grid,a,b) for a,b in split_rows(n,p)]
    start=time.perf_counter()
    chunks=pool.map(work,tasks)
    output=np.concatenate([out for _,out in sorted(chunks)],axis=0)
    elapsed=time.perf_counter()-start
    checksum=float(np.sum(output,dtype=np.float64))
    # Verify output numerically for the exact same input and dimensions.
    reference=stencil_chunk(grid,1,n+1)
    max_err=float(np.max(np.abs(output-reference)))
    if max_err > 1e-12: raise AssertionError('stencil discrepancy: '+str(max_err))
    return elapsed,checksum,max_err


def main():
    mp.set_start_method('spawn',force=True)
    profile=json.loads((ROOT/'results/host_profile.json').read_text())
    params=json.loads((ROOT/'results/salted_params.json').read_text())
    n=params['N'];seed=params['seed']
    physical=profile['physical_cores'] or psutil.cpu_count(logical=False) or 1
    counts=[x for x in [1,2,4,8,16,32] if x<=physical]
    if counts[-1] != physical: counts.append(physical)
    # Spawn/warm-up outside measurement in worker processes.
    stencil_chunk(matrix(8,seed),1,9)
    rows=[]; strong_base=None; weak_base=None
    for p in counts:
        with mp.Pool(processes=p) as pool:
            pool.map(work,[(matrix(8,seed),1,9)]*p)
            t,check,err=run_case(n,p,seed,pool)
            # Weak scaling uses Np = ceil(N sqrt(P)), growing area O(P).
            weak_n=math.ceil(n*math.sqrt(p))
            tw,checkw,errw=run_case(weak_n,p,seed,pool)
        if p==1:strong_base=t; weak_base=tw
        speed=strong_base/t; eff=100*speed/p
        s=((1/speed)-(1/p))/(1-(1/p)) if p>1 else None
        scaled_speed=p*n*n*weak_base/(weak_n*weak_n*tw)
        rows.append([p,n,t,speed,eff,s,check,err,weak_n,tw,scaled_speed,checkw,errw])
        print(f'P={p} strong={t:.4f}s speedup={speed:.3f}; weak={tw:.4f}s scaled_speedup={scaled_speed:.3f}')
    with (ROOT/'results/scaling_metrics.tsv').open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t');w.writerow(['processes','strong_N','strong_seconds','strong_speedup','strong_efficiency_pct','amdahl_serial_fraction','strong_checksum','strong_max_error','weak_N','weak_seconds','weak_scaled_speedup','weak_checksum','weak_max_error']);w.writerows(rows)
    # Per inner cell: multiply center by 4 + four adds + divide by 8 = 6 flops.
    # Pessimistic memory traffic: 5 reads + 1 store of 8 bytes = 48 B/cell.
    intensity=6/48
    # Peak BW is not discoverable reliably from sysctl; do not invent it.
    serial=[r[5] for r in rows if r[5] is not None and r[5]>0]
    fitted=float(np.median(serial)) if serial else None
    summary={'kernel':'5-point Jacobi stencil, one update per cell',
       'floating_point_operations_per_cell':6,'estimated_DRAM_bytes_per_cell':48,
       'arithmetic_intensity_flops_per_byte':intensity,
       'memory_traffic_model':'Conservative streaming 5 loads + 1 store; ignores cache reuse and write allocation',
       'effective_serial_fraction_median_positive':fitted,
       'amdahl_max_speedup':1/fitted if fitted else None,
       'peak_memory_bandwidth_GB_s':None,
       'peak_compute_GFLOP_s':None,
       'roofline_bound':'undetermined from measurements alone',
       'interpretation':'Low arithmetic intensity suggests memory sensitivity; cannot prove memory-bound without peak bandwidth and compute specifications. Pool data serialization also matters.',
       'host_cache_bytes':profile['caches']}
    (ROOT/'results/roofline_summary.json').write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main()
