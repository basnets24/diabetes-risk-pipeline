from pyspark.sql import SparkSession
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import StandardScaler
from pyspark.sql.functions import col, when

# Step 1: Create Spark Session
spark = SparkSession.builder \
    .appName("DiabetesLogisticRegression") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Step 2: Load pre-split stratified data from GCS
TRAIN_PATH = "gs://team10-diabetes-data/features/v2/train_feature_table"

train_df = spark.read.parquet(TRAIN_PATH)

# Step 3: Class weights — computed from train label distribution
counts = {r["diabetes"]: r["count"]
          for r in train_df.groupBy("diabetes").count().collect()}
total = sum(counts.values())
pos   = counts.get(1, 0)
neg   = counts.get(0, 0)

weight_for_1 = neg / total
weight_for_0 = pos / total

print(f"Train rows:                  {total}")
print(f"Weight for diabetic (1):     {weight_for_1:.4f}")
print(f"Weight for non-diabetic (0): {weight_for_0:.4f}")


# add weight column to train only 
train_weighted = train_df.withColumn(
    "classWeight",
    when(col("diabetes") == 1, weight_for_1)
    .otherwise(weight_for_0)
)

# Step 4: Standard scaling — fit on train only, transform all splits
# LR relies on gradient descent; unscaled features (e.g. glucose 80–400 vs binary 0/1)
# cause slow or uneven convergence
scaler = StandardScaler(
    inputCol="features",
    outputCol="scaled_features",
    withMean=True,
    withStd=True
)

scaler_model = scaler.fit(train_weighted)
train_scaled = scaler_model.transform(train_weighted)

# Step 5: Train Logistic Regression
lr = LogisticRegression(
    featuresCol="scaled_features",
    labelCol="diabetes",
    predictionCol="prediction",
    weightCol="classWeight",
    maxIter=20,
    tol=1e-6
)

lr_model = lr.fit(train_scaled)

# Step 6: Convergence diagnostics
# totalIterations tells you where it actually stopped (early if tol was met)
print(f"\nConverged at iteration: {lr_model.summary.totalIterations}")



# Step 7: Save model and scaler to GCS
lr_model.write().overwrite().save("gs://team10-diabetes-data/models/lr_model")
scaler_model.write().overwrite().save("gs://team10-diabetes-data/models/lr_scaler")
print("Model and scaler saved")

# Step 8: Stop Spark
spark.stop()
