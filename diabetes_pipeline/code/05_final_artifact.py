from pyspark.sql import SparkSession
import json
import subprocess

spark = SparkSession.builder \
    .appName("FinalArtifact") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

BUCKET = "gs://team10-diabetes-data"

# ── Build patient-level final table ──────────────────────────────────────────
lr = spark.read.parquet(f"{BUCKET}/predictions/lr_risk_stratified") \
    .select("row_id", "diabetes", "prob_diabetic", "risk_band") \
    .withColumnRenamed("prob_diabetic", "lr_prob_calibrated")

rf = spark.read.parquet(f"{BUCKET}/predictions/rf_scored_test") \
    .select("row_id", "prob_diabetic") \
    .withColumnRenamed("prob_diabetic", "rf_prob")

feats = spark.read.parquet(f"{BUCKET}/features/v2/test_feature_table") \
    .select("row_id", "hbA1c_level", "blood_glucose_level", "bmi", "age", "hypertension", "heart_disease")

final_df = lr.join(rf, on="row_id").join(feats, on="row_id")

OUT_PATH = f"{BUCKET}/predictions/v2_final_dataset"
final_df.write.mode("overwrite").parquet(OUT_PATH)
final_count = final_df.count()
print(f"Final dataset saved: {OUT_PATH} ({final_count} rows)")

# ── Validate evaluation outputs ───────────────────────────────────────────────
EVAL_PATHS = {
    "metrics_lr":            f"{BUCKET}/evaluation/metrics_lr",
    "metrics_rf":            f"{BUCKET}/evaluation/metrics_rf",
    "feature_importance_rf": f"{BUCKET}/evaluation/feature_importance_rf",
    "risk_summary_lr":       f"{BUCKET}/evaluation/risk_summary_lr",
    "risk_aggregation_lr":   f"{BUCKET}/evaluation/risk_aggregation_lr",
}

manifest = {
    "final_dataset": {"path": OUT_PATH, "row_count": final_count},
    "evaluation": {}
}

print("─── Evaluation Path Validation ───")
all_valid = True
for name, path in EVAL_PATHS.items():
    try:
        count = spark.read.option("header", "true").csv(path).count()
        manifest["evaluation"][name] = {"path": path, "row_count": count}
        print(f"  OK      {name}: {count} rows")
    except Exception as e:
        manifest["evaluation"][name] = {"path": path, "status": "MISSING", "error": str(e)}
        print(f"  MISSING {name}: {e}")
        all_valid = False

if all_valid:
    print(f"All {len(EVAL_PATHS)} evaluation outputs confirmed.")
else:
    print("WARNING: some evaluation outputs are missing.")

# ── Save manifest ─────────────────────────────────────────────────────────────
local_manifest = "/tmp/manifest.json"
with open(local_manifest, "w") as f:
    json.dump(manifest, f, indent=2)

subprocess.run(["gsutil", "cp", local_manifest, f"{BUCKET}/manifest.json"])
print(f"Manifest saved: {BUCKET}/manifest.json")

spark.stop()
