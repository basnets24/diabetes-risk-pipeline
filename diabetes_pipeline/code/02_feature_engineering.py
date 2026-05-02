from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import col

# Step 1: Create Spark session
spark = SparkSession.builder \
    .appName("DiabetesFeatureEngineering") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Step 2: Load preprocessed data from GCS
INPUT_PATH = "gs://team10-diabetes-data/processed/df_processed"
df = spark.read.parquet(INPUT_PATH)

# Step 3: Define feature set
FEATURES = ["hbA1c_level", "blood_glucose_level", "bmi", "age", "hypertension", "heart_disease"]
LABEL    = "diabetes"

# Step 4: Stratified 70/10/20 split (train / calibration / test)
# Split per class to preserve the ~8.5% diabetic ratio across all three sets
diabetic     = df.filter(col(LABEL) == 1)
non_diabetic = df.filter(col(LABEL) == 0)

train_pos, cal_pos, test_pos = diabetic.randomSplit([0.7, 0.1, 0.2], seed=42)
train_neg, cal_neg, test_neg = non_diabetic.randomSplit([0.7, 0.1, 0.2], seed=42)

train = train_pos.union(train_neg)
cal   = cal_pos.union(cal_neg)
test  = test_pos.union(test_neg)

# Step 5: Assemble feature vector — all numeric, no encoding needed
assembler = VectorAssembler(
    inputCols=FEATURES,
    outputCol="features"
)

# Step 6: Transform all splits
TRAIN_PATH = "gs://team10-diabetes-data/features/v2/train_feature_table"
CAL_PATH   = "gs://team10-diabetes-data/features/v2/calibration_feature_table"
TEST_PATH  = "gs://team10-diabetes-data/features/v2/test_feature_table"

assembler.transform(train) \
    .select("features", LABEL) \
    .write.mode("overwrite").parquet(TRAIN_PATH)
print(f"Train features saved:       {TRAIN_PATH}")

assembler.transform(cal) \
    .select("features", LABEL) \
    .write.mode("overwrite").parquet(CAL_PATH)
print(f"Calibration features saved: {CAL_PATH}")

assembler.transform(test) \
    .select("row_id", "features", LABEL, *FEATURES) \
    .write.mode("overwrite").parquet(TEST_PATH)
print(f"Test features saved:        {TEST_PATH}")

# Step 7: Stop Spark
spark.stop()
