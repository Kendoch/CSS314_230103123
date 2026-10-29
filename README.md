# CS482 Parallel Computing & Performance Optimization — macOS Python project

This laboratory measures cache-line stride effects, loop order on dense matrix multiplication, false sharing across shared counters, and strong/weak process scaling for a 5-point stencil. Findings must be drawn from **real experiments run on your own Mac**, especially because Apple Silicon's performance/efficiency cores and Python process-spawn overhead affect the results. The verification script checks array agreement, integer counts, and report consistency; it is **not** the instructor's original `verify_outputs.py` (which was not included in the provided document). The demonstration hash in the handout is not an expected digest for your own salted values. Karp–Flatt/Amdahl estimates based on multiprocessing may exceed theoretical bounds when parallel overhead causes slowdown. Roofline classification remains unconfirmed until machine-specific memory-bandwidth and peak-compute values are measured or sourced.

## Run on macOS (Terminal)

```bash
cd ~/Downloads/lab-submission  # change this to where you unpacked the ZIP
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/profile_env.py --student-id YOUR_8_DIGIT_ID
python src/stride_bench.py
python src/dense_kernel.py
python src/false_sharing.py
python src/scaling_study.py
python verify_outputs.py
```

`false_sharing.py` uses 5 million increments **per worker** as required. `scaling_study.py` grows the weak-scaling matrix according to the assignment; memory usage can be high on large-core Macs. If a trial is noisy, repeat it and document that fact rather than modifying output numbers.

## Git checkpoints (run when the corresponding scripts/results are ready)

```bash
git init
git branch -M main
git add . && git commit -m "M0: Environment and salting configuration" && git tag M0-ENV
# run stride_bench.py and dense_kernel.py
git add . && git commit -m "M1: Memory stride and loop interchange benchmarking" && git tag M1-LOCALITY
# run false_sharing.py
git add . && git commit -m "M2: False sharing reproduction and Karp-Flatt analysis" && git tag M2-SHARING
# run scaling_study.py
git add . && git commit -m "M3: Strong and weak scaling evaluation" && git tag M3-SCALING
# run verify_outputs.py
git add . && git commit -m "M4: Final verification and completed practicum submission" && git tag M4-FINAL
# after configuring your course remote:
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main --tags
```

Run commands at each checkpoint rather than copying the whole Git block at the end. The `results/` directory is empty until experiments are executed on your Mac.
