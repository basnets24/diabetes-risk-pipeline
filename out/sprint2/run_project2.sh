#!/usr/bin/env bash 
set -euo pipefail 

IN="/mnt/scratch/CS131_jelenag/projects/team10_sec3/diabetes_dataset.csv"
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
echo "Generating sample of ${SAMPLE_N} at $SAMPLE"  
# Write header
echo "Including the header in the file"
head -n 1 $IN > $SAMPLE
# Randomly sample remaining rows
tail -n +2 "$IN" | shuf -n "$SAMPLE_N" >> "$SAMPLE"
echo "Used shuf for random sampling."


# ---- Frequency tables ----------
# Format: cut -d <DELIM> -f<col> | sort | uniq -c | sort -nr  -> out/freq_<field>.txt

echo "Frequency tables"

# gender (col2)
echo "Calculating frequency table of gender of the participants"
cut -d"$DELIM" -f2 "$IN" | tail -n +2 | sort | uniq -c | sort -nr > "$OUTDIR/freq_gender.txt"
echo "Wrote to $OUTDIR/freq_gender.txt"

# smoking_history (col 12)
echo "Calculating the frequency table of smoking history of the particpants"
cut -d"$DELIM" -f12 "$SAMPLE" | tail -n +2 | sort | uniq -c | sort -nr > "$OUTDIR/freq_smoking_history.txt"
echo "Wrote to $OUTDIR/freq_smoking_history.txt"

# diabetes (col 16)
echo "Calculating the frequency table of presence of diabetes of the participants"
cut -d"$DELIM" -f16 "$IN" | tail -n +2 | sort | uniq -c | sort -nr > "$OUTDIR/freq_diabetes_raw.txt"
echo "Wrote to $OUTDIR/freq_diabetes_raw.txt" 

# year (col 1) 
echo "Calculating the frequency table for the years in which data was collected"
cut -d"$DELIM" -f1 "$IN" | tail -n +2 | sort | uniq -c | sort -r > "$OUTDIR/freq_year.txt"
echo "Wrote to $OUTDIR/freq_year.txt"
echo 

# ---- Top-N entity list (with counts) ----
echo "Calculating TOP N lists" 
# Top locations (col 4)
ENTITY=location
echo "Top $TOP_N $ENTITY that participants belong to"
cut -d"$DELIM" -f4 "$IN" | tail -n +2 | sort | uniq -c | sort -nr | head -n "$TOP_N" > "$OUTDIR/top_${TOP_N}_$ENTITY.txt"
echo "Wrote to $OUTDIR/top_${TOP_N}_$ENTITY.txt"

ENTITY=age
echo "Top $TOP_N $ENTITY that are common among the participants"
cut -d"$DELIM" -f1 "$IN" | tail -n +2 | sort | uniq -c | sort -nr | head -n "$TOP_N" > "$OUTDIR/top_${TOP_N}_$ENTITY.txt"
echo "Wrote to $OUTDIR/top_${TOP_N}_$ENTITY.txt"

ENTITY=blood_glucose_level
echo "Top $TOP_N $ENTITY that are common among the participants"
cut -d"$DELIM" -f15 "$IN" | tail -n +2 | sort | uniq -c | sort -nr | head -n "$TOP_N" > "$OUTDIR/top_${TOP_N}_$ENTITY.txt"
echo "Wrote to $OUTDIR/top_${TOP_N}_$ENTITY.txt"
echo

# ---- Skinny table ( cut and dedupe) -----
echo "Creating a Skinny Table including age, hypertension and diabetes"
{
  echo "age,hypertension,diabetes"
  cut -d"$DELIM" -f3,10,16 "$IN" | tail -n +2 | sort -u
} > "$OUTDIR/skinny_age_hypertension_diabetes_dedup.csv"
echo "Wrote to $OUTDIR/skinny_age_hypertension_diabetes_dedup.csv"
echo

echo "grep examples" 
echo "case-insensitive search for "no info" in smoking_history using grep"
# (We extract col 12, then grep -i)
cut -d"$DELIM" -f12 "$IN" | tail -n +2 | grep -i "no info" | head -n 20 > "$OUTDIR/grep_smoking_noinfo_ci_head.txt" 2> "$OUTDIR/grep_errors.txt" || true 
echo "Wrote $OUTDIR/grep_smoking_noinfo_ci_head.txt (first 20 matches)"

echo "Invert match: values NOT equal to "No Info" (exact case), show top 10"
cut -d"$DELIM" -f12 "$IN" | tail -n +2 | grep -v "^No Info$" | sort | uniq -c | sort -nr | head -n 10 > "$OUTDIR/smoking_excluding_noinfo_top10.txt" 2> "$OUTDIR/grep_errors.txt" 
echo "Wrote $OUTDIR/smoking_excluding_noinfo_top10.txt"
echo 

echo "Optional join: enrich race counts with labels by pasting four race columns into one file"
#Creating ID to race map separately, then paste
cat > race_map.tsv << 'EOF'
1	AfricanAmerican
2	Asian
3	Caucasian
4	Hispanic
5	Others
EOF

# Doing the counts for the race 
{
  tail -n +2 "$IN" | cut -d"$DELIM" -f5 | grep -c '^1$'
  tail -n +2 "$IN" | cut -d"$DELIM" -f6 | grep -c '^1$'
  tail -n +2 "$IN" | cut -d"$DELIM" -f7 | grep -c '^1$'
  tail -n +2 "$IN" | cut -d"$DELIM" -f8 | grep -c '^1$'
  tail -n +2 "$IN" | cut -d"$DELIM" -f9 | grep -c '^1$'
} > race_counts.tsv
paste race_map.tsv race_counts.tsv > "$OUTDIR/mapped_race_frequency.txt"
rm -f race_map.tsv
rm -f race_counts.tsv 
echo "Wrote the join table to $OUTDIR/mapped_race_frequency.txt" 


echo
echo "RUN FINISHED"
