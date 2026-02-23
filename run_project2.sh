#!/usr/bin/env bash 
set -euo pipefail 

IN="../diabetes_dataset.csv"
DELIM=","
OUTDIR="out"
DATA="data"
SAMPLE_N=2000
TOP_N=10

mkdir -p "$OUTDIR"
mkdir -p "$DATA/samples"

LOG="$OUTDIR/run.log"

# Log everything (stdout+stderr) to out/run.log
exec > >(tee "$LOG") 2>&1

echo "RUN STARTED @ $(date)"
echo "Input: $IN"
echo "Output dir: $OUTDIR"
echo 

# ---- Generate a sample ----
# Keep header + random SAMPLE_N rows

SAMPLE="$DATA/samples/sample_${SAMPLE_N}.csv"
echo "Generating sample: $SAMPLE" 
# Write header
head -n 1 $IN > $SAMPLE
# Randomly sample remaining rows
tail -n +2 "$IN" | shuf -n "$SAMPLE_N" >> "$SAMPLE"
echo "Used shuf for random sampling."


# ---- Frequency tables ----------
# Format: cut -d <DELIM> -f<col> | sort | uniq -c | sort -nr  -> out/freq_<field>.txt

echo "Frequency tables"

# gender (col2) 
cut -d"$DELIM" -f2 "$IN" | tail -n +2 | sort | uniq -c | sort -nr > "$OUTDIR/freq_gender.txt"
echo "Wrote $OUTDIR/freq_gender.txt"

# smoking_history (col 12)
cut -d"$DELIM" -f12 "$SAMPLE" | tail -n +2 | sort | uniq -c | sort -nr > "$OUTDIR/freq_smoking_history.txt"
echo "Wrote $OUTDIR/freq_smoking_history.txt"

# diabetes (col 16)
cut -d"$DELIM" -f16 "$IN" | tail -n +2 | sort | uniq -c | sort -nr > "$OUTDIR/freq_diabetes_raw.txt"
echo "Wrote $OUTDIR/freq_diabetes_raw.txt"
echo 

# ---- Top-N entity list (with counts) ----
# Top locations (col 4)
ENTITY=location
echo "Top $TOP_N $ENTITY"
cut -d"$DELIM" -f4 "$IN" | tail -n +2 | sort | uniq -c | sort -nr | head -n "$TOP_N" > "$OUTDIR/top_${TOP_N}_$ENTITY.txt"

# ---- Skinny table ( cut and dedupe) -----
echo "Skinny Table"
{
  echo "age,hypertension,diabetes"
  cut -d"$DELIM" -f3,10,16 "$IN" | tail -n +2 | sort -u
} > "$OUTDIR/skinny_age_hypertension_diabetes_dedup.csv"
echo "Wrote $OUTDIR/skinny_age_hypertension_diabetes_dedup.csv"
echo

echo "grep examples" 
# Case-insensitive search for "no info" in smoking_history
# (We extract col 12, then grep -i)
cut -d"$DELIM" -f12 "$IN" | tail -n +2 | grep -i "no info" | head -n 20 > "$OUTDIR/grep_smoking_noinfo_ci_head.txt" || true 
echo "Wrote $OUTDIR/grep_smoking_noinfo_ci_head.txt (first 20 matches)"

# Invert match: values NOT equal to "No Info" (exact case), show top 10
cut -d"$DELIM" -f12 "$IN" | tail -n +2 | grep -v "^No Info$" | sort | uniq -c | sort -nr | head -n 10 > "$OUTDIR/smoking_excluding_noinfo_top10.txt"
echo "Wrote $OUTDIR/smoking_excluding_noinfo_top10.txt"
echo 

echo "Optional join: enrich diabetes counts with labels"
# Extract ID and count separately, then paste

echo
echo "RUN FINISHED"
