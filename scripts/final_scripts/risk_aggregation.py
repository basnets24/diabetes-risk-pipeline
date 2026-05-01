# Imports
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, round as spark_round

# Step 1: Create Spark Session
spark = SparkSession.builder \
    .appName("DiabetesRiskAggregation") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Step 2: Load predictions (includes risk_category, prob_diabetic, and original feature columns)
PRED_PATH = "gs://team10-diabetes-data/predictions/random_forest"
OUT_BASE  = "gs://team10-diabetes-data/aggregations"

df = spark.read.parquet(PRED_PATH).cache()
row_count = df.count()  # force cache to materialize
print(f"Loaded {row_count} prediction rows")

# Step 3: Aggregate risk by each feature dimension
dimensions = [
    ("bmi_category",  "risk_by_bmi_category"),
    ("age_bucket",    "risk_by_age_bucket"),
    ("hypertension",  "risk_by_hypertension"),
    ("heart_disease", "risk_by_heart_disease"),
    ("comorbidity",   "risk_by_comorbidity"),
]

for dim_col, out_name in dimensions:
    agg = (
        df.groupBy(dim_col, "risk_category")
          .agg(
              count("*").alias("patient_count"),
              spark_round(avg("prob_diabetic"), 4).alias("avg_prob_diabetic")
          )
          .orderBy(dim_col, "risk_category")
    )
    agg.write.mode("overwrite").parquet(f"{OUT_BASE}/{out_name}/")
    print(f"Saved: {OUT_BASE}/{out_name}/")

df.unpersist()

# Step 4: Stop Spark
spark.stop()
