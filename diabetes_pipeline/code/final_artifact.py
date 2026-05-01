# Imports
from pyspark.sql import SparkSession
import json
import subprocess

# Step 1: Create Spark Session (no models — lightweight join + validation job)
spark = SparkSession.builder \
    .appName("DiabetesFinalArtifact") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

BUCKET   = "gs://team10-diabetes-data"
LR_PATH  = f"{BUCKET}/predictions/logistic_regression"
RF_PATH  = f"{BUCKET}/predictions/random_forest"
OUT_PATH = f"{BUCKET}/predictions/final_dataset"

AGG_PATHS = {
    "risk_by_bmi_category":  f"{BUCKET}/aggregations/risk_by_bmi_category",
    "risk_by_age_bucket":    f"{BUCKET}/aggregations/risk_by_age_bucket",
    "risk_by_hypertension":  f"{BUCKET}/aggregations/risk_by_hypertension",
    "risk_by_heart_disease": f"{BUCKET}/aggregations/risk_by_heart_disease",
    "risk_by_comorbidity":   f"{BUCKET}/aggregations/risk_by_comorbidity",
    "feature_importance":    f"{BUCKET}/aggregations/feature_importance",
}

# Step 2: Load LR predictions — has all original columns + lr outputs
lr_df = spark.read.parquet(LR_PATH) \
    .withColumnRenamed("prediction",    "lr_prediction") \
    .withColumnRenamed("prob_diabetic", "lr_prob_diabetic") \
    .withColumnRenamed("risk_category", "lr_risk_category") \
    .drop("features", "probability")

# Step 3: Load RF predictions — select only the rf-specific outputs for join
rf_df = spark.read.parquet(RF_PATH) \
    .select("row_id", "prediction", "prob_diabetic", "risk_category") \
    .withColumnRenamed("prediction",    "rf_prediction") \
    .withColumnRenamed("prob_diabetic", "rf_prob_diabetic") \
    .withColumnRenamed("risk_category", "rf_risk_category")

# Step 4: Join on row_id and write in one pass 
final_df = lr_df.join(rf_df, on="row_id")
final_df.write.mode("overwrite").parquet(OUT_PATH)
final_count = spark.read.parquet(OUT_PATH).count()
print(f"Final dataset saved: {OUT_PATH} ({final_count} rows)")

# Step 5: Validate all aggregation paths
manifest = {
    "final_dataset": {"path": OUT_PATH, "row_count": final_count},
    "aggregations":  {}
}

print("─── Aggregation Path Validation ───")
all_valid = True
for name, path in AGG_PATHS.items():
    try:
        row_count = spark.read.parquet(path).count()
        manifest["aggregations"][name] = {"path": path, "row_count": row_count}
        print(f"  OK  {name}: {row_count} rows")
    except Exception as e:
        manifest["aggregations"][name] = {"path": path, "status": "MISSING", "error": str(e)}
        print(f"  MISSING  {name}: {e}")
        all_valid = False

if all_valid:
    print(f"All {len(AGG_PATHS)} aggregation paths confirmed.")
else:
    print("WARNING: some aggregation paths are missing.")

# Step 6: Save manifest to GCS
local_manifest = "/tmp/manifest.json"
with open(local_manifest, "w") as f:
    json.dump(manifest, f, indent=2)

subprocess.run(["gsutil", "cp", local_manifest, f"{BUCKET}/manifest.json"])
print(f"Manifest saved: {BUCKET}/manifest.json")

# Step 7: Stop Spark
spark.stop()
