# Imports
from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col, when

# Step 1: Create Spark Session
spark = SparkSession.builder \
    .appName("DiabetesRandomForest") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Step 2: Load pre-split stratified data from GCS
TRAIN_PATH = "gs://team10-diabetes-data/features/train_feature_table"
TEST_PATH  = "gs://team10-diabetes-data/features/test_feature_table"

test_df = spark.read.parquet(TEST_PATH).coalesce(2)

# Step 3: Class weights 
counts = {r["diabetes"]: r["count"]
          for r in spark.read.parquet(TRAIN_PATH).groupBy("diabetes").count().collect()}
total = sum(counts.values())
pos   = counts.get(1, 0)
neg   = counts.get(0, 0)

print(f"Train rows: {total}")
print(f"Weight for diabetic (1):     {neg / total:.4f}")
print(f"Weight for non-diabetic (0): {pos / total:.4f}")

# Step 4: Train Random Forest — repartition(2) for tree building
train_df = spark.read.parquet(TRAIN_PATH).repartition(2).withColumn("classWeight",
    when(col("diabetes") == 1, neg / total).otherwise(pos / total)
)

rf = RandomForestClassifier(
    labelCol="diabetes",
    featuresCol="features",
    predictionCol="prediction",
    weightCol="classWeight",
    numTrees=20,
    maxDepth=3,
    maxBins=16,
    subsamplingRate=0.7,
    seed=42
)

rf_model = rf.fit(train_df)
print("Model trained")

# Step 5: Generate predictions and assign risk categories
predictions = rf_model.transform(test_df)
predictions = predictions.withColumn("prob_diabetic", vector_to_array(col("probability")).getItem(1))
predictions = predictions.withColumn(
    "risk_category",
    when(col("prob_diabetic") >= 0.7, "High Risk")
    .when(col("prob_diabetic") >= 0.3, "Medium Risk")
    .otherwise("Low Risk")
)

# Step 5b: Save predictions in one pass — no cache, single GCS write scan
# (keep probability so eval job can compute AUC with BinaryClassificationEvaluator)
save_cols = [c for c in predictions.columns if c not in ("rawPrediction", "classWeight")]
predictions.select(save_cols).write.mode("overwrite").parquet(
    "gs://team10-diabetes-data/predictions/random_forest"
)
print("Predictions saved")

# Step 6: Save model
rf_model.write().overwrite().save(
    "gs://team10-diabetes-data/models/random_forest"
)
print("Model saved")

# Step 7: Stop Spark
spark.stop()
