#!/usr/bin/env python3
"""
assumption_test.py
Usage:
  ./scripts/assumption_test.py <DATASET_PATH> <DELIM>

Example:
  ./scripts/assumption_test.py data/cleaned_data.csv ","
Outputs:
  out/evidence/assumption_test_id_repeats_top20.txt
  out/evidence/assumption_test_category_distinct_sample.txt
"""
import sys
import csv
from collections import Counter
import os

if len(sys.argv) < 3:
    print("Usage: {} <DATASET_PATH> <DELIM>".format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)

DATASET = sys.argv[1]
DELIM = sys.argv[2]

OUT_DIR = "out/evidence"
os.makedirs(OUT_DIR, exist_ok=True)

# adjust these column names or indices if needed
# if header exists, we will detect header and choose defaults
ID_FIELD = None        # if None, will try to detect 'id' or use first column
CATEGORY_FIELD = None  # if None, will try to detect 'category' or use second column

def sniff_header(path, delim):
    with open(path, newline='') as fh:
        rdr = csv.reader(fh, delimiter=delim)
        first = next(rdr, None)
        return first

header = sniff_header(DATASET, DELIM)
use_header = False
if header:
    # simple heuristic: treat first row as header if any non-numeric tokens
    if any(not cell.isdigit() for cell in header):
        use_header = True

id_idx = 0
cat_idx = 1
if use_header:
    hdr = [h.strip().lower() for h in header]
    # try to find common names
    for name in ['id','patient_id','subject_id','record_id']:
        if name in hdr:
            id_idx = hdr.index(name)
            break
    for name in ['category','diag','diagnosis','condition','label','disease','cohort','race','age_bucket']:
        if name in hdr:
            cat_idx = hdr.index(name)
            break

# counters
id_counter = Counter()
cat_values = set()

with open(DATASET, newline='') as fh:
    rdr = csv.reader(fh, delimiter=DELIM)
    if use_header:
        next(rdr, None)
    for row in rdr:
        if len(row) == 0:
            continue
        # safe index access
        if id_idx < len(row):
            id_counter[row[id_idx].strip()] += 1
        if cat_idx < len(row):
            val = row[cat_idx].strip()
            if val != "":
                cat_values.add(val)

# write top repeated IDs
out1 = os.path.join(OUT_DIR, "assumption_test_id_repeats_top20.txt")
with open(out1, "w") as f:
    f.write("top repeated IDs (count, id)\n")
    for count, _id in id_counter.most_common(20):
        f.write(f"{count}\t{_id}\n")

# write category distinct sample (up to 100)
out2 = os.path.join(OUT_DIR, "assumption_test_category_distinct_sample.txt")
with open(out2, "w") as f:
    f.write("sample distinct category values (up to 100)\n")
    for i, val in enumerate(sorted(cat_values)):
        if i >= 100:
            break
        f.write(f"{val}\n")

print("Wrote:", out1)
print("Wrote:", out2)
