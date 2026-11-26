"""download_data.py - fetches the PhysioNet records used by the project into ./data

    python3 download_data.py                 # record 100 + NSTDB 'em' (what the report uses)
    python3 download_data.py 101 103 112     # also download extra MIT-BIH records

Sources (open access, Open Data Commons Attribution License v1.0):
  MIT-BIH Arrhythmia Database v1.0.0       https://physionet.org/content/mitdb/1.0.0/
  MIT-BIH Noise Stress Test Database v1.0.0 https://physionet.org/content/nstdb/1.0.0/
"""
import os
import sys
import wfdb

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

records = ["100"] + [r for r in sys.argv[1:] if r != "100"]
for rec in records:
    print(f"MIT-BIH record {rec} ...")
    wfdb.dl_files("mitdb", DATA, [f"{rec}.hea", f"{rec}.dat", f"{rec}.atr"])
print("NSTDB electrode-motion record 'em' ...")
wfdb.dl_files("nstdb", DATA, ["em.hea", "em.dat"])

expected = [f"{r}.{e}" for r in records for e in ("hea", "dat", "atr")] + ["em.hea", "em.dat"]
missing = [f for f in expected if not os.path.exists(os.path.join(DATA, f))]
if missing:
    sys.exit(f"Missing after download: {missing}")
print(f"Done. Files in {DATA}: {sorted(os.listdir(DATA))}")
