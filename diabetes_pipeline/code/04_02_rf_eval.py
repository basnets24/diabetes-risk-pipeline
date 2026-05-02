from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

spark = SparkSession.builder \
    .appName("RF_Evaluation") \
    .config("spark.sql.shuffle.partitions", "8") \
    .config("spark.eventLog.enabled", "false") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

rf_model = RandomForestClassificationModel.load("gs://team10-diabetes-data/models/rf_model")

test_pd = (
    rf_model.transform(spark.read.parquet("gs://team10-diabetes-data/features/v2/test_feature_table"))
    .select("row_id", "diabetes", vector_to_array(col("probability"))[1].alias("prob_diabetic"))
    .toPandas()
)

auc_roc = roc_auc_score(test_pd["diabetes"], test_pd["prob_diabetic"])
auc_pr  = average_precision_score(test_pd["diabetes"], test_pd["prob_diabetic"])
brier   = brier_score_loss(test_pd["diabetes"], test_pd["prob_diabetic"])

print(f"AUC-ROC: {auc_roc:.4f}  AUC-PR: {auc_pr:.4f}  Brier: {brier:.4f}")

spark.createDataFrame(test_pd[["row_id", "diabetes", "prob_diabetic"]]) \
    .write.mode("overwrite").parquet("gs://team10-diabetes-data/predictions/rf_scored_test")

spark.createDataFrame([{
    "auc_roc": float(round(auc_roc, 4)),
    "auc_pr":  float(round(auc_pr,  4)),
    "brier":   float(round(brier,   4)),
}]).coalesce(1).write.mode("overwrite").option("header", "true").csv(
    "gs://team10-diabetes-data/evaluation/metrics_rf"
)
print("Evaluation saved")

spark.stop()
