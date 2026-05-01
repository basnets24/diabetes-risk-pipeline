# Imports
from pyspark.sql import SparkSession
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col, when

# Step 1: Create Spark Session
spark = SparkSession.builder \
    .appName("DiabetesLogisticRegression") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Step 2: Load pre-split stratified data from GCS
TRAIN_PATH = "gs://team10-diabetes-data/features/train_feature_table"
TEST_PATH  = "gs://team10-diabetes-data/features/test_feature_table"

test_df = spark.read.parquet(TEST_PATH)

# Step 3: Class weights 
counts = {r["diabetes"]: r["count"]
          for r in spark.read.parquet(TRAIN_PATH).groupBy("diabetes").count().collect()}
total = sum(counts.values())
pos   = counts.get(1, 0)
neg   = counts.get(0, 0)

weight_for_1 = neg / total
weight_for_0 = pos / total

print(f"Train rows: {total}")
print(f"Weight for diabetic (1):     {weight_for_1:.4f}")
print(f"Weight for non-diabetic (0): {weight_for_0:.4f}")

# Step 4: Train Logistic Regression — read train fresh so heap is free for gradient computation
train_df = spark.read.parquet(TRAIN_PATH).withColumn("classWeight",
    when(col("diabetes") == 1, weight_for_1).otherwise(weight_for_0)
)

lr = LogisticRegression(
    featuresCol="features",
    labelCol="diabetes",
    predictionCol="prediction",
    weightCol="classWeight",
    maxIter=100
)
lr_model = lr.fit(train_df)

# Step 5: Generate predictions and assign risk categories
predictions = lr_model.transform(test_df)
predictions = predictions.withColumn("prob_diabetic", vector_to_array(col("probability")).getItem(1))
predictions = predictions.withColumn(
    "risk_category",
    when(col("prob_diabetic") >= 0.7, "High Risk")
    .when(col("prob_diabetic") >= 0.3, "Medium Risk")
    .otherwise("Low Risk")
)

# Step 6: Save predictions in one pass 
# (keep probability so eval job can compute AUC with BinaryClassificationEvaluator)
save_cols = [c for c in predictions.columns if c not in ("rawPrediction", "classWeight")]
predictions.select(save_cols).write.mode("overwrite").parquet(
    "gs://team10-diabetes-data/predictions/logistic_regression"
)
print("Predictions saved")

# Step 7: Save model
lr_model.write().overwrite().save(
    "gs://team10-diabetes-data/models/logistic_regression"
)
print("Model saved")

# Step 8: Stop Spark
spark.stop()
