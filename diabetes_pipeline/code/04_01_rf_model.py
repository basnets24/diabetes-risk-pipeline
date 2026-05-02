from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassifier
from pyspark.sql.functions import col, when

spark = SparkSession.builder \
    .appName("RF_Train") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

train_df = spark.read.parquet("gs://team10-diabetes-data/features/v2/train_feature_table")

counts = {r["diabetes"]: r["count"]
          for r in train_df.groupBy("diabetes").count().collect()}
total = sum(counts.values())
pos   = counts.get(1, 0)
neg   = counts.get(0, 0)

print(f"Train rows:                  {total}")
print(f"Weight for diabetic (1):     {neg / total:.4f}")
print(f"Weight for non-diabetic (0): {pos / total:.4f}")

train_weighted = train_df.withColumn(
    "classWeight",
    when(col("diabetes") == 1, neg / total).otherwise(pos / total)
)

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="diabetes",
    predictionCol="prediction",
    weightCol="classWeight",
    numTrees=20,
    maxDepth=3,
    maxBins=16,
    subsamplingRate=0.7,
    seed=42,
)

rf_model = rf.fit(train_weighted)
print(f"Trees trained: {rf_model.getNumTrees}")

rf_model.write().overwrite().save("gs://team10-diabetes-data/models/rf_model")
print("Model saved")

spark.stop()
