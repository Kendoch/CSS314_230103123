"""Mac/Linux CPU and cache profiling. Unknown specifications stay null."""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
import psutil
from salt import get_student_params

ROOT = Path(__file__).resolve().parents[1]


def sysctl(key):
    try:
        return subprocess.check_output(['sysctl', '-n', key], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def number(s):
    if not s:
        return None
    m = re.match(r'^\s*(\d+)', str(s))
    return int(m.group(1)) if m else None


def describe_host():
    mac = sys.platform == 'darwin'
    brand = sysctl('machdep.cpu.brand_string') if mac else None
    if not brand and mac:
        brand = platform.processor() or sysctl('hw.model')
    if not brand:
        try:
            brand = next(line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name'))
        except (OSError, StopIteration):
            brand = platform.processor()
    caches = {}
    if mac:
        caches = {key: number(sysctl(val)) for key, val in {
            'L1_data_bytes': 'hw.l1dcachesize', 'L2_bytes': 'hw.l2cachesize',
            'L3_bytes': 'hw.l3cachesize', 'cache_line_bytes': 'hw.cachelinesize'}.items()}
    else:
        base = Path('/sys/devices/system/cpu/cpu0/cache')
        for idx in base.glob('index*'):
            try:
                kind = (idx / 'type').read_text().strip()
                level = (idx / 'level').read_text().strip()
                raw = (idx / 'size').read_text().strip().upper()
                m = re.match(r'(\d+)([KMG]?)', raw)
                size = int(m[1]) * {'': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3}[m[2]] if m else None
                key = f'L{level}_data_bytes' if level == '1' and kind == 'Data' else f'L{level}_bytes'
                if kind != 'Instruction': caches[key] = size
                caches['cache_line_bytes'] = number((idx / 'coherency_line_size').read_text())
            except OSError: pass
    physical = psutil.cpu_count(logical=False)
    logical = psutil.cpu_count(logical=True)
    freq = psutil.cpu_freq()
    base_hz = number(sysctl('hw.cpufrequency')) if mac else None
    return {'cpu_model': brand, 'microarchitecture': platform.machine(),
            'base_frequency_hz': base_hz, 'observed_frequency_mhz': freq.current if freq else None,
            'physical_cores': physical, 'logical_threads': logical,
            'smt_or_heterogeneous_note': 'On Apple Silicon, logical/physical counts may represent performance and efficiency cores, not SMT.' if mac else None,
            'caches': caches, 'os': platform.platform(), 'kernel': platform.release(),
            'python': sys.version, 'python_implementation': platform.python_implementation(),
            'memory_bytes': psutil.virtual_memory().total,
            'note': 'Cache sizes reported by sysctl may be per cluster; missing values are not assumed.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--student-id', required=True)
    args = parser.parse_args()
    out = ROOT / 'results'; out.mkdir(exist_ok=True)
    params = get_student_params(args.student_id)
    for filename, value in [('host_profile.json', describe_host()), ('salted_params.json', params)]:
        (out / filename).write_text(json.dumps(value, indent=2) + '\n')
    print('Saved host profile and salted params:', params)

if __name__ == '__main__': main()
