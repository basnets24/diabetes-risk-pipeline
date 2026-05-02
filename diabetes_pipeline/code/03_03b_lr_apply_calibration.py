from pyspark.sql import SparkSession
from pyspark.ml.classification import LogisticRegressionModel
from pyspark.ml.feature import StandardScalerModel, VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col

spark = SparkSession.builder \
    .appName("LR_ApplyCalibration") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

lr_model     = LogisticRegressionModel.load("gs://team10-diabetes-data/models/lr_model")
scaler_model = StandardScalerModel.load("gs://team10-diabetes-data/models/lr_scaler")
platt_model  = LogisticRegressionModel.load("gs://team10-diabetes-data/models/platt_model")
assembler    = VectorAssembler(inputCols=["prob_diabetic_raw"], outputCol="platt_features")


def calibrate_and_save(feature_path, output_path, id_cols):
    # LR score — immediately project down to only the columns we need
    scored = (
        lr_model.transform(
            scaler_model.transform(spark.read.parquet(feature_path))
        )
        .select(
            *id_cols,
            "diabetes",
            vector_to_array(col("probability"))[1].alias("prob_diabetic_raw"),
        )
    )
    # Platt calibration on the tiny (2-3 col) DataFrame
    calibrated = (
        platt_model.transform(assembler.transform(scored))
        .withColumn("prob_diabetic", vector_to_array(col("platt_probability"))[1])
        .select(*id_cols, "diabetes", "prob_diabetic_raw", "prob_diabetic", "platt_prediction")
    )
    calibrated.write.mode("overwrite").parquet(output_path)

    row = calibrated.selectExpr(
        "avg(prob_diabetic_raw) as pre_avg",
        "avg(prob_diabetic)     as post_avg",
        "avg(diabetes)          as true_prev",
    ).collect()[0]
    print(f"Saved -> {output_path}")
    print(f"  pre-cal avg:  {row['pre_avg']:.4f}")
    print(f"  post-cal avg: {row['post_avg']:.4f}  (should be close to true prevalence)")
    print(f"  true prev:    {row['true_prev']:.4f}")


calibrate_and_save(
    "gs://team10-diabetes-data/features/v2/calibration_feature_table",
    "gs://team10-diabetes-data/predictions/lr_calibrated_cal",
    id_cols=[],
)

calibrate_and_save(
    "gs://team10-diabetes-data/features/v2/test_feature_table",
    "gs://team10-diabetes-data/predictions/lr_calibrated_test",
    id_cols=["row_id"],
)

spark.stop()
