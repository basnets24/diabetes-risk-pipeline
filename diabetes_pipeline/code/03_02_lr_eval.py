from pyspark.sql import SparkSession
from pyspark.ml.classification import LogisticRegressionModel
from pyspark.ml.feature import StandardScalerModel
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col, when
from sklearn.metrics import precision_recall_curve
import numpy as np

spark = SparkSession.builder \
    .appName("LR_Evaluation") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

lr_model     = LogisticRegressionModel.load("gs://team10-diabetes-data/models/lr_model")
scaler_model = StandardScalerModel.load("gs://team10-diabetes-data/models/lr_scaler")

cal_preds = (
    lr_model.transform(scaler_model.transform(
        spark.read.parquet("gs://team10-diabetes-data/features/v2/calibration_feature_table")
    ))
    .withColumn("prob_diabetic_raw", vector_to_array(col("probability"))[1])
    .select("prob_diabetic_raw", "diabetes")
)

test_preds = (
    lr_model.transform(scaler_model.transform(
        spark.read.parquet("gs://team10-diabetes-data/features/v2/test_feature_table")
    ))
    .withColumn("prob_diabetic_raw", vector_to_array(col("probability"))[1])
    .select("row_id", "prob_diabetic_raw", "diabetes")
)

# ── Threshold tuning on cal set (F2-max) ──────────────────────────────────────
cal_pd = cal_preds.toPandas()
precision, recall, thresholds = precision_recall_curve(
    cal_pd["diabetes"], cal_pd["prob_diabetic_raw"]
)
f2 = 5 * (precision[:-1] * recall[:-1]) / (4 * precision[:-1] + recall[:-1] + 1e-9)
best_threshold = float(thresholds[np.argmax(f2)])

print(f"Tuned threshold (F2-max on cal set): {best_threshold:.4f}")
print(f"Best F2 on cal set: {f2.max():.4f}")

# ── Confusion matrix on test set ──────────────────────────────────────────────
test_scored = test_preds.withColumn(
    "prediction", when(col("prob_diabetic_raw") >= best_threshold, 1).otherwise(0)
)

cm = {(r["diabetes"], r["prediction"]): r["count"]
      for r in test_scored.groupBy("diabetes", "prediction").count().collect()}
tp = cm.get((1, 1), 0);  tn = cm.get((0, 0), 0)
fp = cm.get((0, 1), 0);  fn = cm.get((1, 0), 0)
n_pos = tp + fn;  n_neg = tn + fp;  n_total = tp + tn + fp + fn

sensitivity = tp / n_pos          if n_pos     > 0 else 0.0
specificity = tn / n_neg          if n_neg     > 0 else 0.0
precision_v = tp / (tp + fp)      if (tp + fp) > 0 else 0.0
f1_score    = 2 * precision_v * sensitivity / (precision_v + sensitivity + 1e-9)
accuracy    = (tp + tn) / n_total

print(f"\n─── Test Set Confusion Matrix ───")
print(f"  TP={tp}  TN={tn}  FP={fp}  FN={fn}")
print(f"  Sensitivity: {sensitivity:.4f}  Specificity: {specificity:.4f}")
print(f"  Precision:   {precision_v:.4f}  F1: {f1_score:.4f}  Accuracy: {accuracy:.4f}")

# ── Save confusion matrix to GCS ──────────────────────────────────────────────
spark.createDataFrame([
    {"metric": "TP",          "value": float(tp)},
    {"metric": "TN",          "value": float(tn)},
    {"metric": "FP",          "value": float(fp)},
    {"metric": "FN",          "value": float(fn)},
    {"metric": "Sensitivity", "value": round(sensitivity, 4)},
    {"metric": "Specificity", "value": round(specificity, 4)},
    {"metric": "Precision",   "value": round(precision_v, 4)},
    {"metric": "F1",          "value": round(f1_score,   4)},
    {"metric": "Accuracy",    "value": round(accuracy,   4)},
    {"metric": "Threshold",   "value": round(best_threshold, 4)},
]).coalesce(1).write.mode("overwrite").option("header", "true").csv(
    "gs://team10-diabetes-data/evaluation/confusion_matrix_lr"
)
print("Evaluation saved")

spark.stop()
