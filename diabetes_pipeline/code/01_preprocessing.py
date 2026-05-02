from pyspark.sql import SparkSession
from pyspark.sql.functions import col, monotonically_increasing_id

# Step 1: Create Spark session
spark = SparkSession.builder \
    .appName("DiabetesPreprocessing") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .config("spark.sql.adaptive.enabled", True) \
    .getOrCreate()

# Step 2: Load raw CSV from GCS
INPUT_PATH  = "gs://team10-diabetes-data/raw/diabetes_dataset.csv"
OUTPUT_PATH = "gs://team10-diabetes-data/processed/df_processed"

df_raw = spark.read.csv(INPUT_PATH, header=True, inferSchema=True)
print(f"Raw row count: {df_raw.count()}")

# Step 3: Drop nulls on the columns we actually use
REQUIRED_COLS = ["hbA1c_level", "blood_glucose_level", "bmi", "age",
                 "hypertension", "heart_disease", "diabetes"]

df_clean = df_raw.na.drop(subset=REQUIRED_COLS)

# Step 4: Range and validity filters
df_filtered = df_clean.filter(
    (col("diabetes").isin(0, 1))         &
    (col("hypertension").isin(0, 1))     &
    (col("heart_disease").isin(0, 1))    &
    (col("bmi").between(10.0, 80.0))     &
    (col("age").between(0.0, 120.0))     &
    (col("hbA1c_level").between(3.5, 15.0))       &
    (col("blood_glucose_level").between(20, 600))
)

dropped = df_raw.count() - df_filtered.count()
print(f"Rows after filtering: {df_filtered.count()}  (dropped {dropped})")

# Step 5: Assign row ID and narrow to the clean feature set consumed by 02_feature_engineering.py
final_df = df_filtered \
    .withColumn("row_id", monotonically_increasing_id()) \
    .select("row_id", *REQUIRED_COLS)

# Step 6: Save to GCS
final_df.write.mode("overwrite").parquet(OUTPUT_PATH)
print(f"Saved → {OUTPUT_PATH}")

# Step 7: Stop Spark
spark.stop()
