from pyspark.sql import SparkSession
from pyspark.ml.classification import LogisticRegression, LogisticRegressionModel
from pyspark.ml.feature import StandardScalerModel, VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col

spark = SparkSession.builder \
    .appName("LR_Calibration") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
spark.sparkContext.setCheckpointDir("gs://team10-diabetes-data/checkpoints/lr_calibration")

lr_model     = LogisticRegressionModel.load("gs://team10-diabetes-data/models/lr_model")
scaler_model = StandardScalerModel.load("gs://team10-diabetes-data/models/lr_scaler")

# Score cal set — drop ALL feature columns immediately, keep only 2 cols
cal_scored = (
    lr_model.transform(
        scaler_model.transform(
            spark.read.parquet("gs://team10-diabetes-data/features/v2/calibration_feature_table")
        )
    )
    .select(
        col("diabetes"),
        vector_to_array(col("probability"))[1].alias("prob_diabetic_raw"),
    )
)

# Assemble for Platt, then checkpoint to materialise to GCS and free executor memory
assembler = VectorAssembler(inputCols=["prob_diabetic_raw"], outputCol="platt_features")
cal_platt = (
    assembler.transform(cal_scored)
    .select("diabetes", "prob_diabetic_raw", "platt_features")
    .checkpoint()
)

row = cal_platt.selectExpr("avg(prob_diabetic_raw) as pre_avg", "avg(diabetes) as prev").collect()[0]
print(f"Pre-calibration avg prob: {row['pre_avg']:.3f}  True prevalence: {row['prev']:.3f}")

platt_model = LogisticRegression(
    featuresCol="platt_features",
    labelCol="diabetes",
    predictionCol="platt_prediction",
    probabilityCol="platt_probability",
    rawPredictionCol="platt_raw_prediction",
    maxIter=25,
    tol=1e-4,
).fit(cal_platt)

platt_model.write().overwrite().save("gs://team10-diabetes-data/models/platt_model")
print("Platt model saved")

del cal_platt
spark.stop()
