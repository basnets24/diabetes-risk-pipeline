# Imports
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.sql.functions import col, when, monotonically_increasing_id

# Step 1: Create Spark session
spark = SparkSession.builder \
    .appName("DiabetesFeatureEngineering") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Step 2: Load data from Google Cloud Storage
INPUT_PATH="gs://team10-diabetes-data/processed/final_df"
df=spark.read.parquet(INPUT_PATH)

# Step 3: Assign row ID and create Comorbidity Flag
df_with_flag = df.withColumn("row_id", monotonically_increasing_id()) \
                 .withColumn("comorbidity",
                     when((col("hypertension") == 1) & (col("heart_disease") == 1), 1).otherwise(0)
                 )

# Step 4: Stratified Split (keeps 8.5% diabetic ratio in both splits)
diabetic     = df_with_flag.filter(col("diabetes") == 1)
non_diabetic = df_with_flag.filter(col("diabetes") == 0)

train_diabetic,     test_diabetic     = diabetic.randomSplit([0.8, 0.2], seed=42)
train_non_diabetic, test_non_diabetic = non_diabetic.randomSplit([0.8, 0.2], seed=42)

train = train_diabetic.union(train_non_diabetic).cache()
test  = test_diabetic.union(test_non_diabetic)

# Step 5: Encode Categorical Columns (Text -> Numbers -> One-Hot Vectors)
categorical_cols=["age_bucket", "bmi_category"]

# Creating StringIndexer (text -> numeric index)
indexers=[
    StringIndexer(
    inputCol=c,
    outputCol=f"{c}_index",
    handleInvalid="keep"
)
    for c in categorical_cols
]

# Creating OneHotEncoders (index -> binary vector)
encoders=[
    OneHotEncoder(
        inputCol=f"{c}_index",
        outputCol=f"{c}_ohe",
        handleInvalid="keep"
    )
    for c in categorical_cols
]

# Step 6: Vector Assembler (Combine All features into ONE Vector column)
feature_columns=[
    "age_bucket_ohe",       # One-hot encoded
    "bmi_category_ohe",     # One-hot encoded
    "hypertension",         # Original binary
    "heart_disease",        # Original binary
    "comorbidity",          # New binary flag
    "bmi"                   # Original numeric column
]
assembler=VectorAssembler(
    inputCols=feature_columns, # List of columns to combine
    outputCol="features",       # Name of combined vector column
    handleInvalid="keep"
)

# Step 7: Build and Fit Pipeline on TRAIN only (fit only on train to prevent data leakage)
pipeline = Pipeline(stages=indexers + encoders + [assembler])
pipeline_model = pipeline.fit(train)

# Step 8: Save train features — transform directly into write, no intermediate cache
TRAIN_OUTPUT = "gs://team10-diabetes-data/features/train_feature_table"
TEST_OUTPUT  = "gs://team10-diabetes-data/features/test_feature_table"

pipeline_model.transform(train) \
    .select("features", "diabetes") \
    .write.mode("overwrite").parquet(TRAIN_OUTPUT)
train.unpersist()
print(f"Train features saved: {TRAIN_OUTPUT}")

# Step 9: Transform test — single write action, no cache needed
test_features = pipeline_model.transform(test)
test_cols = [c for c in test_features.columns
             if not c.endswith("_index") and not c.endswith("_ohe")]
test_features.select(test_cols).write.mode("overwrite").parquet(TEST_OUTPUT)
print(f"Test features saved: {TEST_OUTPUT}")

# Step 10: Stop Spark Session
spark.stop()