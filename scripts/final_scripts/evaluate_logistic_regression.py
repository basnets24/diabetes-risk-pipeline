# Imports
from pyspark.sql import SparkSession
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

# Create Spark Session
spark=SparkSession.builder.appName("DiabetesLREvaluation").getOrCreate()

# Load the saved predictions
PREDS_PATH="gs://team10-diabetes-data/predictions/logistic_regression"
predictions=spark.read.parquet(PREDS_PATH)

# TICKET 101: ROC-AUC Evaluation
binary_eval=BinaryClassificationEvaluator(labelCol="diabetes", rawPredictionCol="probability", metricName="areaUnderROC")
auc=binary_eval.evaluate(predictions)
print(f"Logistic Regression AUC: {auc}")

# TICKET 102: Precision, Recall, F1, Accuracy
multi_eval=MulticlassClassificationEvaluator(labelCol="diabetes", predictionCol="prediction")
precision=multi_eval.evaluate(predictions, {multi_eval.metricName: "weightedPrecision"})
recall=multi_eval.evaluate(predictions, {multi_eval.metricName: "weightedRecall"})
f1=multi_eval.evaluate(predictions, {multi_eval.metricName: "f1"})
# Accuracy is optional (AUC matters more) as not included in original ticket, feel free to remove it
accuracy=multi_eval.evaluate(predictions, {multi_eval.metricName: "accuracy"})
print(f"Precision: {precision:.4f} | Recall: {recall:.4f} | F1 Score: {f1:.4f} | Accuracy: {accuracy:.4f}")

# TICKET 103: Confusion Matrix
print("Confusion Matrix for Logistic Regression:")
cm=predictions.groupBy("diabetes", "prediction").count()
cm.show()

# Saving the confusion matrix to GCS
CM_PATH="gs://team10-diabetes-data/evaluation/lr_confusion_matrix"
cm.write.mode("overwrite").parquet(CM_PATH)
print(f"SUCCESS: Confusion matrix saved to {CM_PATH}")

# Stop Spark
spark.stop()