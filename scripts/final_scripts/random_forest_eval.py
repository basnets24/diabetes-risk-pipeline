# Imports
from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import csv
import subprocess

# Step 1: Create Spark Session
spark = SparkSession.builder \
    .appName("DiabetesRandomForestEval") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

PRED_PATH  = "gs://team10-diabetes-data/predictions/random_forest"
MODEL_PATH = "gs://team10-diabetes-data/models/random_forest"

# Step 2: Load saved predictions
predictions = spark.read.parquet(PRED_PATH).cache()
print(f"Prediction rows loaded: {predictions.count()}")

print("─── Risk Category Distribution ───")
predictions.groupBy("risk_category").count().orderBy("risk_category").show()
predictions.select("diabetes", "prob_diabetic", "risk_category", "prediction").show(10)

# Step 3: Confusion Matrix — single groupBy scan
cm = {(r["diabetes"], int(r["prediction"])): r["count"]
      for r in predictions.groupBy("diabetes", "prediction").count().collect()}
tp = cm.get((1, 1), 0)
tn = cm.get((0, 0), 0)
fp = cm.get((0, 1), 0)
fn = cm.get((1, 0), 0)

print("─── Confusion Matrix ───")
print(f"                 Predicted 0    Predicted 1")
print(f"Actual 0 (neg)   TN={tn:<8}   FP={fp}")
print(f"Actual 1 (pos)   FN={fn:<8}   TP={tp}")

n_pos = tp + fn
n_neg = tn + fp
n_total = tp + tn + fp + fn

sensitivity = tp / n_pos if n_pos > 0 else 0.0
specificity = tn / n_neg if n_neg > 0 else 0.0
fpr         = fp / n_neg if n_neg > 0 else 0.0

print(f"\nSensitivity: {sensitivity:.4f}")
print(f"Specificity: {specificity:.4f}")
print(f"FPR:         {fpr:.4f}")

# Step 4: Evaluate — AUC only (all other metrics derived from confusion matrix)
auc = BinaryClassificationEvaluator(labelCol="diabetes", rawPredictionCol="probability", metricName="areaUnderROC").evaluate(predictions)

prec_1 = tp / (tp + fp) if (tp + fp) > 0 else 0.0
prec_0 = tn / (tn + fn) if (tn + fn) > 0 else 0.0
rec_1  = sensitivity
rec_0  = specificity
f1_1   = 2 * prec_1 * rec_1 / (prec_1 + rec_1) if (prec_1 + rec_1) > 0 else 0.0
f1_0   = 2 * prec_0 * rec_0 / (prec_0 + rec_0) if (prec_0 + rec_0) > 0 else 0.0

accuracy  = (tp + tn) / n_total
precision = (prec_0 * n_neg + prec_1 * n_pos) / n_total
recall    = (rec_0  * n_neg + rec_1  * n_pos) / n_total
f1        = (f1_0   * n_neg + f1_1   * n_pos) / n_total

print("─── Evaluation Metrics ───")
print(f"AUC-ROC:   {auc:.4f}")
print(f"F1 Score:  {f1:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"Accuracy:  {accuracy:.4f}")

# Step 5: Save confusion matrix CSV
confusion_rows = [
    ("TP",          float(tp)),
    ("TN",          float(tn)),
    ("FP",          float(fp)),
    ("FN",          float(fn)),
    ("Sensitivity", round(sensitivity, 4)),
    ("Specificity", round(specificity, 4)),
    ("FPR",         round(fpr, 4))
]

local_cm = "/tmp/confusion_matrix_rf.csv"
with open(local_cm, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "value"])
    writer.writerows(confusion_rows)

subprocess.run(["gsutil", "cp", local_cm,
    "gs://team10-diabetes-data/evaluation/confusion_matrix_rf.csv"])
print("Confusion matrix saved")

# Step 6: Feature Importance Ranking — load model, read names from predictions schema
rf_model = RandomForestClassificationModel.load(MODEL_PATH)

meta = predictions.schema["features"].metadata.get("ml_attr", {})
name_map = {}
for attr_list in meta.get("attrs", {}).values():
    for attr in attr_list:
        name_map[attr["idx"]] = attr["name"]
n_features = meta.get("num_attrs", len(name_map))
feature_names_full = [name_map.get(i, f"feature_{i}") for i in range(n_features)]

importances = rf_model.featureImportances
ranked = sorted(
    enumerate(zip(feature_names_full, importances.toArray()), 1),
    key=lambda x: x[1][1],
    reverse=True
)

print("─── Feature Importance Ranking ───")
for rank, (name, score) in ranked:
    print(f"{rank}. {name}: {score:.4f}")

fi_df = spark.createDataFrame(
    [(rank, name, round(float(score), 4)) for rank, (name, score) in ranked],
    ["rank", "feature_name", "importance_score"]
)
fi_df.write.mode("overwrite").parquet(
    "gs://team10-diabetes-data/aggregations/feature_importance/"
)
print("Feature importance saved")

predictions.unpersist()

# Step 7: Stop Spark
spark.stop()
