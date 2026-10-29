"""Independent format/consistency checks; not the professor-supplied verifier."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
R=ROOT/'results'

def readtsv(name):
    with (R/name).open(newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def check():
    profile=json.loads((R/'host_profile.json').read_text())
    params=json.loads((R/'salted_params.json').read_text())
    assert profile['physical_cores'] and params['N'] in range(1024,1537,64)
    print('[PASS] Milestone 0: Profile and salted parameters')
    stride=readtsv('stride_results.tsv')
    assert {int(row['stride']) for row in stride}=={1,2,4,8,16,32,64,128}
    for row in stride:
        assert int(row['elements_touched'])== (params['buffer_elements']+int(row['stride'])-1)//int(row['stride'])
        assert float(row['checksum'])==int(row['elements_touched'])
    loop=json.loads((R/'loop_interchange.json').read_text())
    assert loop['allclose_atol_1e-12'] and loop['max_absolute_error']<=1e-12
    assert loop['baseline_sha256_rounded_6']==loop['interchanged_sha256_rounded_6']
    print('[PASS] Milestone 1: Stride checks and matrix numerical digest')
    sharing=readtsv('false_sharing_karp_flatt.tsv')
    assert len(sharing)==12
    for row in sharing:
        assert int(row['total_count'])==int(row['processes'])*int(row['iterations_per_process'])
        if int(row['processes'])>1:
            p=int(row['processes']);s=float(row['speedup'])
            assert abs(float(row['karp_flatt'])-((1/s)-(1/p))/(1-(1/p)))<1e-8
    print('[PASS] Milestone 2: Counters and Karp-Flatt calculations')
    scaling=readtsv('scaling_metrics.tsv')
    assert scaling
    for row in scaling:
        assert float(row['strong_max_error'])<=1e-12 and float(row['weak_max_error'])<=1e-12
        assert float(row['strong_speedup'])>0
    roofline=json.loads((R/'roofline_summary.json').read_text())
    assert roofline['arithmetic_intensity_flops_per_byte']==0.125
    print('[PASS] Milestone 3: Stencil comparisons and arithmetic intensity')
    # A salted receipt over the actual datasets, not a fabricated preset hash.
    files=['host_profile.json','salted_params.json','stride_results.tsv','loop_interchange.json',
        'false_sharing_karp_flatt.tsv','scaling_metrics.tsv','roofline_summary.json']
    hasher=hashlib.sha256(params['student_id'].encode())
    for name in files:
        hasher.update(name.encode());hasher.update((R/name).read_bytes())
    receipt='SHA256:'+hasher.hexdigest()+'\n'
    (R/'verification_receipt.sig').write_text(receipt)
    print('Verification passed. Receipt:', receipt.strip())

if __name__=='__main__':check()
