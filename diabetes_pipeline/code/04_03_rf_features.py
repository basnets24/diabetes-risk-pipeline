from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassificationModel

FEATURE_NAMES = ["hbA1c_level", "blood_glucose_level", "bmi", "age", "hypertension", "heart_disease"]

spark = SparkSession.builder \
    .appName("RF_FeatureImportance") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

rf_model = RandomForestClassificationModel.load("gs://team10-diabetes-data/models/rf_model")

importances = rf_model.featureImportances.toArray()
fi = sorted(zip(FEATURE_NAMES, importances), key=lambda x: x[1], reverse=True)

for rank, (name, score) in enumerate(fi, 1):
    print(f"  {rank}. {name:<22} {score:.4f}")

spark.createDataFrame([
    {"rank": rank, "feature": name, "importance": float(round(score, 4))}
    for rank, (name, score) in enumerate(fi, 1)
]).coalesce(1).write.mode("overwrite").option("header", "true").csv(
    "gs://team10-diabetes-data/evaluation/feature_importance_rf"
)
print("Feature importance saved")

spark.stop()
