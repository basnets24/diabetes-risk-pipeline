from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, mean
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, precision_recall_curve
import pandas as pd
import numpy as np

spark = SparkSession.builder \
    .appName("LR_RiskStratification") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

cal_pd = (
    spark.read.parquet("gs://team10-diabetes-data/predictions/lr_calibrated_cal")
    .select("prob_diabetic", "diabetes")
    .toPandas()
)

test_pd = (
    spark.read.parquet("gs://team10-diabetes-data/predictions/lr_calibrated_test")
    .select("prob_diabetic", "diabetes")
    .toPandas()
)

# ── AUC ───────────────────────────────────────────────────────────────────────
auc_roc = roc_auc_score(test_pd["diabetes"], test_pd["prob_diabetic"])
auc_pr  = average_precision_score(test_pd["diabetes"], test_pd["prob_diabetic"])

print(f"AUC-ROC: {auc_roc:.4f}  AUC-PR: {auc_pr:.4f}")

# ── Calibration ───────────────────────────────────────────────────────────────
brier = brier_score_loss(test_pd["diabetes"], test_pd["prob_diabetic"])

test_pd["decile"] = pd.qcut(test_pd["prob_diabetic"], q=10, labels=False, duplicates="drop")
calib_table = (
    test_pd.groupby("decile")
    .agg(n=("diabetes", "count"), avg_pred=("prob_diabetic", "mean"), actual_rate=("diabetes", "mean"))
    .reset_index()
)
calib_table["gap"] = (calib_table["avg_pred"] - calib_table["actual_rate"]).round(4)

print(f"\nBrier score: {brier:.4f}")
print(f"\n--- Calibration Table (test set, deciles) ---")
print(f"  {'decile':>6}  {'n':>6}  {'avg_pred':>9}  {'actual_rate':>11}  {'gap':>6}")
for _, row in calib_table.iterrows():
    print(f"  {int(row['decile']):>6}  {int(row['n']):>6}  {row['avg_pred']:>9.4f}  {row['actual_rate']:>11.4f}  {row['gap']:>+6.4f}")

# ── Confusion matrix (calibrated, F2-tuned threshold on cal set) ─────────────
precision_arr, recall_arr, thresholds_arr = precision_recall_curve(
    cal_pd["diabetes"], cal_pd["prob_diabetic"]
)
f2 = 5 * (precision_arr[:-1] * recall_arr[:-1]) / (4 * precision_arr[:-1] + recall_arr[:-1] + 1e-9)
best_threshold = float(thresholds_arr[np.argmax(f2)])

test_pd["prediction"] = (test_pd["prob_diabetic"] >= best_threshold).astype(int)
tp = int(((test_pd["prediction"] == 1) & (test_pd["diabetes"] == 1)).sum())
tn = int(((test_pd["prediction"] == 0) & (test_pd["diabetes"] == 0)).sum())
fp = int(((test_pd["prediction"] == 1) & (test_pd["diabetes"] == 0)).sum())
fn = int(((test_pd["prediction"] == 0) & (test_pd["diabetes"] == 1)).sum())
n_pos = tp + fn;  n_neg = tn + fp;  n_total = tp + tn + fp + fn

sensitivity = tp / n_pos          if n_pos     > 0 else 0.0
specificity = tn / n_neg          if n_neg     > 0 else 0.0
precision_v = tp / (tp + fp)      if (tp + fp) > 0 else 0.0
f1_score    = 2 * precision_v * sensitivity / (precision_v + sensitivity + 1e-9)
accuracy    = (tp + tn) / n_total

print(f"\nCalibrated threshold (F2-max on cal set): {best_threshold:.4f}")
print(f"─── Confusion Matrix (calibrated probs) ───")
print(f"  TP={tp}  TN={tn}  FP={fp}  FN={fn}")
print(f"  Sensitivity: {sensitivity:.4f}  Specificity: {specificity:.4f}")
print(f"  Precision:   {precision_v:.4f}  F1: {f1_score:.4f}  Accuracy: {accuracy:.4f}")

# ── Risk stratification ───────────────────────────────────────────────────────
low_thresh  = float(np.percentile(cal_pd["prob_diabetic"], 80))
high_thresh = float(np.percentile(cal_pd["prob_diabetic"], 90))

print(f"\nRisk thresholds (cal p80/p90):  Medium >= {low_thresh:.4f},  High >= {high_thresh:.4f}")

test_stratified = (
    spark.read.parquet("gs://team10-diabetes-data/predictions/lr_calibrated_test")
    .withColumn(
        "risk_band",
        when(col("prob_diabetic") >= high_thresh, "High")
        .when(col("prob_diabetic") >= low_thresh,  "Medium")
        .otherwise("Low"),
    )
)

test_stratified.write.mode("overwrite").parquet(
    "gs://team10-diabetes-data/predictions/lr_risk_stratified"
)

summary_df = (
    test_stratified
    .groupBy("risk_band")
    .agg(count("*").alias("n"), mean("prob_diabetic").alias("avg_prob"), mean("diabetes").alias("diabetic_rate"))
    .orderBy("avg_prob")
)

print("\n--- Risk Band Summary (test set) ---")
for r in summary_df.collect():
    print(f"  {r['risk_band']:6s}  n={r['n']:6d}  avg_prob={r['avg_prob']:.3f}  diabetic_rate={r['diabetic_rate']:.3f}")

# ── Save ──────────────────────────────────────────────────────────────────────
summary_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(
    "gs://team10-diabetes-data/evaluation/risk_summary_lr"
)

spark.createDataFrame(calib_table).coalesce(1) \
    .write.mode("overwrite").option("header", "true").csv(
        "gs://team10-diabetes-data/evaluation/calibration_table_lr"
    )

spark.createDataFrame([{
    "auc_roc":     round(auc_roc,     4),
    "auc_pr":      round(auc_pr,      4),
    "brier":       round(brier,       4),
    "threshold":   round(best_threshold, 4),
    "sensitivity": round(sensitivity, 4),
    "specificity": round(specificity, 4),
    "precision":   round(precision_v, 4),
    "f1":          round(f1_score,    4),
    "accuracy":    round(accuracy,    4),
    "tp": tp, "tn": tn, "fp": fp, "fn": fn,
}]).coalesce(1).write.mode("overwrite").option("header", "true").csv(
    "gs://team10-diabetes-data/evaluation/metrics_lr"
)

print("Evaluation saved")
spark.stop()
